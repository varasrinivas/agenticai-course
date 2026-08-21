"""
Legacy data-access layer for the Meridian UCC filing portal.

Written against Oracle in 2011 and barely touched since. Every method
below contains at least one construct that will not run on PostgreSQL.
This file is INPUT to the `appsql-rewriter` subagent -- it is never
edited in place; the subagent emits a unified diff into artifacts/.

Known Oracle-isms planted here (the rewriter should find all of them):
  - ROWNUM top-N paging            -> LIMIT / OFFSET
  - NVL / NVL2                     -> COALESCE
  - DECODE                         -> CASE
  - (+) outer join operator        -> LEFT JOIN
  - CONNECT BY PRIOR               -> WITH RECURSIVE
  - SYSDATE / SYSTIMESTAMP         -> now() / current_timestamp
  - FROM DUAL                      -> omit the FROM clause
  - MERGE                          -> INSERT ... ON CONFLICT
  - TO_CHAR with Oracle masks      -> to_char, mask differences on RR/HH24
  - Named bind parameters :name    -> %(name)s for psycopg
  - Implicit '' IS NULL comparison -> explicit ( x IS NULL OR x = '' )
"""

import os
import logging

import cx_Oracle  # legacy driver; PostgreSQL port moves to psycopg[binary]

log = logging.getLogger(__name__)


def _connect():
    """Open a connection using the legacy TNS descriptor."""
    dsn = os.environ.get("ORACLE_DSN")
    if not dsn:
        raise RuntimeError("ORACLE_DSN is not set")
    return cx_Oracle.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=dsn,
    )


def recent_filings(state_code, limit=50):
    """Most recent filings for a state.

    ROWNUM in an inline view is the Oracle top-N idiom. The filter has to
    be applied AFTER the sort, which is why the ORDER BY sits in the
    subquery -- a detail that trips up naive rewrites.
    """
    sql = """
        SELECT *
          FROM (SELECT f.filing_id,
                       f.filing_number,
                       f.filed_date,
                       NVL(f.page_count, 0)        AS page_count,
                       NVL(d.debtor_name, 'UNKNOWN') AS debtor_name
                  FROM ucc_filing f,
                       ucc_debtor d
                 WHERE f.filing_id = d.filing_id(+)
                   AND f.state_code = :state_code
                 ORDER BY f.filed_date DESC)
         WHERE ROWNUM <= :row_limit
    """
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, state_code=state_code, row_limit=limit)
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur]
        except cx_Oracle.DatabaseError:
            log.exception("recent_filings failed for state=%s", state_code)
            raise
        finally:
            cur.close()


def filing_status_report(as_of=None):
    """Status rollup using DECODE and an Oracle date mask."""
    sql = """
        SELECT f.state_code,
               DECODE(f.status,
                      'ACTIVE',     'Open',
                      'LAPSED',     'Expired',
                      'TERMINATED', 'Closed',
                      'Unknown')                          AS status_label,
               COUNT(*)                                   AS filing_count,
               TO_CHAR(MAX(f.filed_date), 'MM/DD/RR HH24:MI') AS newest,
               NVL2(MAX(f.filing_fee), 'has fees', 'no fees') AS fee_flag
          FROM ucc_filing f
         WHERE f.filed_date <= NVL(:as_of, SYSDATE)
         GROUP BY f.state_code, f.status
         ORDER BY f.state_code
    """
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, as_of=as_of)
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur]
        except cx_Oracle.DatabaseError:
            log.exception("filing_status_report failed")
            raise
        finally:
            cur.close()


def amendment_chain(filing_id):
    """Walk the amendment tree for one filing.

    CONNECT BY PRIOR has no PostgreSQL equivalent. The rewrite is a
    WITH RECURSIVE CTE, and LEVEL / SYS_CONNECT_BY_PATH / CONNECT_BY_ISLEAF
    all have to be rebuilt by hand -- depth is a counter carried through
    the recursion, the path is string concatenation, and is-leaf needs a
    NOT EXISTS against the children.
    """
    sql = """
        SELECT a.amendment_id,
               a.amendment_type,
               a.amendment_date,
               LEVEL                                        AS depth,
               SYS_CONNECT_BY_PATH(a.amendment_type, ' > ')  AS chain_path,
               CONNECT_BY_ISLEAF                             AS is_leaf
          FROM ucc_amendment a
         WHERE a.filing_id = :filing_id
         START WITH a.parent_amendment_id IS NULL
         CONNECT BY PRIOR a.amendment_id = a.parent_amendment_id
         ORDER SIBLINGS BY a.amendment_date
    """
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, filing_id=filing_id)
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur]
        except cx_Oracle.DatabaseError:
            log.exception("amendment_chain failed for filing_id=%s", filing_id)
            raise
        finally:
            cur.close()


def debtors_missing_address_line_2():
    """Debtors with no second address line.

    THIS IS THE QUERY THE EMPTY-STRING TRAP BREAKS.

    On Oracle, `mailing_address_2 IS NULL` also matches rows that were
    written as '' -- because Oracle stores '' as NULL. Port the data
    naively and those rows arrive in PostgreSQL as zero-length strings,
    this predicate stops matching them, and the report silently loses
    about 1,400 rows. Nothing errors. The number just gets quietly wrong.

    The correct PostgreSQL rewrite is:
        WHERE d.mailing_address_2 IS NULL OR d.mailing_address_2 = ''
    ...but the better fix is upstream: load the data so Oracle NULLs
    stay NULL, and then this predicate needs no change at all.
    """
    sql = """
        SELECT d.debtor_id,
               d.debtor_name,
               d.city,
               d.state_code
          FROM ucc_debtor d
         WHERE d.mailing_address_2 IS NULL
         ORDER BY d.debtor_name
    """
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql)
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur]
        except cx_Oracle.DatabaseError:
            log.exception("debtors_missing_address_line_2 failed")
            raise
        finally:
            cur.close()


def server_time():
    """Trivial, but DUAL does not exist in PostgreSQL."""
    with _connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT SYSTIMESTAMP FROM dual")
            return cur.fetchone()[0]
        except cx_Oracle.DatabaseError:
            log.exception("server_time failed")
            raise
        finally:
            cur.close()
