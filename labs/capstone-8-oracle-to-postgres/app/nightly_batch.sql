-- =====================================================================
-- nightly_batch.sql -- run by cron at 02:15 against the legacy database.
--
-- INPUT to the `appsql-rewriter` subagent. This is the densest single
-- file of Oracle-isms in the app: SQL*Plus directives, DUAL, ROWNUM,
-- (+), CONNECT BY, MERGE, DECODE, NVL, TO_CHAR masks, sequence .NEXTVAL,
-- and a package call.
--
-- Note the SQL*Plus commands at the top -- `SET SERVEROUTPUT ON`,
-- `WHENEVER SQLERROR`, `EXIT` -- none of which psql understands. Those
-- are not SQL and the rewriter should map them to psql equivalents
-- (\set ON_ERROR_STOP, \echo) rather than trying to translate them as
-- statements.
-- =====================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED
SET FEEDBACK OFF
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

-- 1. Refresh the state rollup ----------------------------------------
BEGIN
  DBMS_MVIEW.REFRESH('MV_STATE_ROLLUP', 'C');
END;
/

-- 2. Lapse anything past its date ------------------------------------
DECLARE
  v_lapsed NUMBER;
BEGIN
  pkg_filing_maint.lapse_expired_filings(TRUNC(SYSDATE), v_lapsed);
  DBMS_OUTPUT.PUT_LINE('Lapsed ' || v_lapsed || ' filings');
END;
/

-- 3. Refresh the per-state sync watermark ----------------------------
MERGE INTO state_sos_source t
USING (SELECT f.state_code,
              MAX(f.filed_date) AS newest
         FROM ucc_filing f
        GROUP BY f.state_code) s
   ON (t.state_code = s.state_code)
 WHEN MATCHED THEN
   UPDATE SET t.last_sync = CAST(s.newest AS TIMESTAMP);

COMMIT;

-- 4. Nightly exception report ----------------------------------------
--    (+) outer join, DECODE, NVL, TO_CHAR mask, date subtraction.
SELECT f.filing_number,
       NVL(s.state_name, 'UNMAPPED')                        AS state_name,
       DECODE(f.status, 'ACTIVE', 'OPEN', 'CLOSED')         AS simple_status,
       TO_CHAR(f.filed_date, 'DD-MON-RR HH24:MI:SS')        AS filed_display,
       TRUNC(SYSDATE) - TRUNC(f.filed_date)                 AS age_days
  FROM ucc_filing f,
       state_sos_source s
 WHERE f.state_code = s.state_code(+)
   AND f.status = 'ACTIVE'
   AND f.lapse_date < SYSDATE          -- ACTIVE but already lapsed
 ORDER BY age_days DESC;

-- 5. Deep amendment chains (more than two levels) --------------------
SELECT filing_id,
       COUNT(*) AS chain_length
  FROM (SELECT a.filing_id,
               a.amendment_id,
               LEVEL AS depth
          FROM ucc_amendment a
         START WITH a.parent_amendment_id IS NULL
         CONNECT BY PRIOR a.amendment_id = a.parent_amendment_id)
 GROUP BY filing_id
HAVING COUNT(*) > 2
 ORDER BY chain_length DESC;

-- 6. Top 25 debtors by exposure --------------------------------------
SELECT *
  FROM (SELECT d.debtor_name,
               COUNT(*)                        AS filings,
               SUM(NVL(f.filing_fee, 0))       AS fees,
               pkg_risk_calc.score_debtor(d.debtor_name) AS risk_score
          FROM ucc_debtor d
          JOIN ucc_filing f ON f.filing_id = d.filing_id
         WHERE f.status = 'ACTIVE'
         GROUP BY d.debtor_name
         ORDER BY SUM(NVL(f.filing_fee, 0)) DESC)
 WHERE ROWNUM <= 25;

-- 7. Heartbeat -------------------------------------------------------
SELECT 'nightly_batch complete at ' || TO_CHAR(SYSTIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')
  FROM dual;

EXIT SUCCESS
