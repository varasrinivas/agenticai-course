-- =====================================================================
-- PL/SQL packages -- the part the retired DBAs wrote in 2004.
--
-- PostgreSQL has no packages. The translation is: one schema per
-- package, one function per public procedure/function, package-level
-- variables become either function parameters or a session GUC.
--
-- PKG_FILING_MAINT.log_audit uses PRAGMA AUTONOMOUS_TRANSACTION. There
-- is no safe PostgreSQL equivalent. The plsql-converter subagent must
-- REFUSE this one and queue it for manual review. Silently dropping the
-- pragma changes the semantics: audit rows would start disappearing on
-- rollback, which is the exact opposite of what an audit log is for.
-- =====================================================================

ALTER SESSION SET CURRENT_SCHEMA = MERIDIAN;

CREATE OR REPLACE PACKAGE pkg_risk_calc AS
  -- Package-level constant: becomes a PostgreSQL immutable function or
  -- an inlined literal.
  c_blanket_weight  CONSTANT NUMBER := 0.35;

  FUNCTION score_debtor (p_debtor_name IN VARCHAR2) RETURN NUMBER;
  FUNCTION risk_level   (p_score IN NUMBER) RETURN VARCHAR2;
  FUNCTION active_filing_count (p_debtor_name IN VARCHAR2) RETURN NUMBER;
END pkg_risk_calc;
/

CREATE OR REPLACE PACKAGE BODY pkg_risk_calc AS

  FUNCTION active_filing_count (p_debtor_name IN VARCHAR2) RETURN NUMBER IS
    v_count NUMBER;
  BEGIN
    -- NVL, UPPER, and an implicit join. Straightforward to convert.
    SELECT COUNT(*)
      INTO v_count
      FROM ucc_filing f, ucc_debtor d
     WHERE f.filing_id = d.filing_id
       AND UPPER(d.debtor_name) = UPPER(NVL(p_debtor_name, '~none~'))
       AND f.status = 'ACTIVE';
    RETURN v_count;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RETURN 0;
  END active_filing_count;

  FUNCTION score_debtor (p_debtor_name IN VARCHAR2) RETURN NUMBER IS
    v_active    NUMBER;
    v_blanket   NUMBER;
    v_states    NUMBER;
    v_score     NUMBER;
  BEGIN
    v_active := active_filing_count(p_debtor_name);

    -- DBMS_LOB.INSTR on a CLOB -- becomes position() over text.
    SELECT COUNT(*)
      INTO v_blanket
      FROM ucc_filing f
      JOIN ucc_debtor d ON d.filing_id = f.filing_id
     WHERE UPPER(d.debtor_name) = UPPER(p_debtor_name)
       AND f.status = 'ACTIVE'
       AND DBMS_LOB.INSTR(f.collateral_desc, 'all assets') > 0;

    SELECT COUNT(DISTINCT f.state_code)
      INTO v_states
      FROM ucc_filing f
      JOIN ucc_debtor d ON d.filing_id = f.filing_id
     WHERE UPPER(d.debtor_name) = UPPER(p_debtor_name);

    -- LEAST/GREATEST exist in both, with the same semantics.
    v_score := LEAST(1,
                 (v_active * 0.08)
               + (v_blanket * c_blanket_weight)
               + (GREATEST(v_states - 1, 0) * 0.05));

    RETURN ROUND(v_score, 4);
  END score_debtor;

  FUNCTION risk_level (p_score IN NUMBER) RETURN VARCHAR2 IS
  BEGIN
    -- DECODE-style CASE. Converts cleanly.
    RETURN CASE
             WHEN p_score >= 0.66 THEN 'HIGH'
             WHEN p_score >= 0.33 THEN 'MEDIUM'
             ELSE 'LOW'
           END;
  END risk_level;

END pkg_risk_calc;
/

CREATE OR REPLACE PACKAGE pkg_filing_maint AS
  PROCEDURE log_audit (p_filing_id IN NUMBER,
                       p_action    IN VARCHAR2,
                       p_detail    IN VARCHAR2);

  PROCEDURE lapse_expired_filings (p_as_of IN DATE DEFAULT SYSDATE,
                                   p_count OUT NUMBER);

  PROCEDURE merge_state_source (p_state_code IN VARCHAR2,
                                p_state_name IN VARCHAR2,
                                p_format     IN VARCHAR2);
END pkg_filing_maint;
/

CREATE OR REPLACE PACKAGE BODY pkg_filing_maint AS

  -- ###################################################################
  -- AUTONOMOUS TRANSACTION -- NO POSTGRESQL EQUIVALENT.
  -- The point of the pragma is that the audit row COMMITS even if the
  -- calling business transaction rolls back. In PostgreSQL you need
  -- dblink, a background worker, or a redesign (write audit rows from
  -- the application layer, outside the transaction).
  -- The converter must flag this, not translate it.
  -- ###################################################################
  PROCEDURE log_audit (p_filing_id IN NUMBER,
                       p_action    IN VARCHAR2,
                       p_detail    IN VARCHAR2) IS
    PRAGMA AUTONOMOUS_TRANSACTION;
  BEGIN
    INSERT INTO filing_audit (audit_id, filing_id, action, detail)
    VALUES (seq_audit_id.NEXTVAL, p_filing_id, p_action, p_detail);
    COMMIT;
  END log_audit;

  PROCEDURE lapse_expired_filings (p_as_of IN DATE DEFAULT SYSDATE,
                                   p_count OUT NUMBER) IS
    -- BULK COLLECT into a collection -- becomes an array or a plain
    -- set-based UPDATE ... RETURNING in PostgreSQL.
    TYPE t_id_list IS TABLE OF ucc_filing.filing_id%TYPE;
    v_ids t_id_list;
  BEGIN
    SELECT filing_id
      BULK COLLECT INTO v_ids
      FROM ucc_filing
     WHERE status = 'ACTIVE'
       AND lapse_date IS NOT NULL
       AND lapse_date < p_as_of;

    FORALL i IN 1 .. v_ids.COUNT
      UPDATE ucc_filing
         SET status = 'LAPSED'
       WHERE filing_id = v_ids(i);

    p_count := v_ids.COUNT;

    FOR i IN 1 .. v_ids.COUNT LOOP
      log_audit(v_ids(i), 'LAPSE', 'Auto-lapsed by nightly batch');
    END LOOP;
  END lapse_expired_filings;

  -- MERGE -- becomes INSERT ... ON CONFLICT DO UPDATE.
  PROCEDURE merge_state_source (p_state_code IN VARCHAR2,
                                p_state_name IN VARCHAR2,
                                p_format     IN VARCHAR2) IS
  BEGIN
    MERGE INTO state_sos_source t
    USING (SELECT p_state_code AS state_code FROM dual) s
       ON (t.state_code = s.state_code)
     WHEN MATCHED THEN
       UPDATE SET t.state_name  = p_state_name,
                  t.feed_format = p_format,
                  t.last_sync   = SYSTIMESTAMP
     WHEN NOT MATCHED THEN
       INSERT (state_code, state_name, feed_format, last_sync)
       VALUES (p_state_code, p_state_name, p_format, SYSTIMESTAMP);
  END merge_state_source;

END pkg_filing_maint;
/
