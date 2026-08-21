-- =====================================================================
-- Views and one materialized view.
--
-- These are the densest Oracle-ism samples in the schema: (+) outer
-- joins, CONNECT BY, ROWNUM, DECODE, NVL, TO_CHAR masks, and DUAL all
-- appear here. The appsql-rewriter subagent is scored partly on these.
-- =====================================================================

ALTER SESSION SET CURRENT_SCHEMA = MERIDIAN;

-- ---------------------------------------------------------------------
-- V_FILING_SUMMARY
-- Traps: (+) outer join syntax, DECODE, NVL, TO_CHAR with an Oracle
--        format mask, and a DATE arithmetic expression (date - date
--        returns a NUMBER of days in Oracle; in PostgreSQL it returns
--        an interval).
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_filing_summary AS
SELECT f.filing_id,
       f.filing_number,
       f.state_code,
       s.state_name,
       DECODE(f.filing_type,
              'UCC1',      'Financing Statement',
              'UCC3_AMD',  'Amendment',
              'UCC3_CONT', 'Continuation',
              'UCC3_TERM', 'Termination',
              'Other')                                AS filing_type_label,
       TO_CHAR(f.filed_date, 'MM/DD/YYYY HH24:MI')     AS filed_display,
       NVL(f.page_count, 0)                           AS page_count,
       NVL(TO_CHAR(f.filing_fee, '9990.00'), 'N/A')   AS fee_display,
       f.lapse_date - f.filed_date                    AS lifespan_days,
       CASE WHEN f.lapse_date < SYSDATE THEN 'Y' ELSE 'N' END AS is_expired
  FROM ucc_filing f,
       state_sos_source s
 WHERE f.state_code = s.state_code(+);   -- Oracle outer join operator

-- ---------------------------------------------------------------------
-- V_DEBTOR_EXPOSURE
-- Traps: ROWNUM in an inline view (the classic Oracle top-N idiom),
--        and a scalar subquery against DUAL.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_debtor_exposure AS
SELECT *
  FROM (SELECT d.debtor_name,
               COUNT(*)                     AS filing_count,
               SUM(NVL(f.filing_fee, 0))    AS total_fees,
               MAX(f.filed_date)            AS most_recent,
               (SELECT SYSDATE FROM dual)   AS as_of
          FROM ucc_debtor d
          JOIN ucc_filing f ON f.filing_id = d.filing_id
         WHERE f.status = 'ACTIVE'
         GROUP BY d.debtor_name
         ORDER BY COUNT(*) DESC)
 WHERE ROWNUM <= 100;

-- ---------------------------------------------------------------------
-- V_AMENDMENT_CHAIN
-- Trap: CONNECT BY PRIOR hierarchical query with LEVEL and
--       SYS_CONNECT_BY_PATH. Becomes WITH RECURSIVE, but the ordering
--       and the path-building are both hand-work.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_amendment_chain AS
SELECT a.amendment_id,
       a.filing_id,
       a.parent_amendment_id,
       a.amendment_type,
       a.amendment_date,
       LEVEL                                             AS depth,
       SYS_CONNECT_BY_PATH(a.amendment_type, ' > ')      AS chain_path,
       CONNECT_BY_ISLEAF                                 AS is_leaf
  FROM ucc_amendment a
 START WITH a.parent_amendment_id IS NULL
 CONNECT BY PRIOR a.amendment_id = a.parent_amendment_id;

-- ---------------------------------------------------------------------
-- MV_STATE_ROLLUP
-- Trap: materialized view with REFRESH ON DEMAND. PostgreSQL has
--       materialized views but no query rewrite and no fast refresh --
--       the refresh strategy has to change, not just the DDL.
-- ---------------------------------------------------------------------
CREATE MATERIALIZED VIEW mv_state_rollup
BUILD IMMEDIATE
REFRESH COMPLETE ON DEMAND
AS
SELECT f.state_code,
       s.state_name,
       COUNT(*)                                              AS total_filings,
       SUM(DECODE(f.status, 'ACTIVE', 1, 0))                 AS active_filings,
       SUM(DECODE(f.status, 'LAPSED', 1, 0))                 AS lapsed_filings,
       ROUND(AVG(NVL(f.filing_fee, 0)), 2)                   AS avg_fee,
       MAX(f.filed_date)                                     AS newest_filing
  FROM ucc_filing f
  JOIN state_sos_source s ON s.state_code = f.state_code
 GROUP BY f.state_code, s.state_name;
