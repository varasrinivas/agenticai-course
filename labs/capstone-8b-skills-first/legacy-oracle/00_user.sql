-- =====================================================================
-- Creates the MERIDIAN schema owner.
--
-- gvenzl/oracle-free runs every *.sql in /container-entrypoint-initdb.d
-- in lexical order, as SYS, connected to the FREEPDB1 pluggable
-- database. So this file runs first and everything after it can rely on
-- `ALTER SESSION SET CURRENT_SCHEMA = MERIDIAN`.
--
-- The MIGRATION_READER user at the bottom is what the agent connects
-- as. It has SELECT on the schema and nothing else -- so even if the
-- PreToolUse read-only hook were removed, the database itself would
-- still refuse a write. Defense in depth: the hook is the fast, legible
-- guardrail; the grant is the one that survives a code bug.
-- =====================================================================

ALTER SESSION SET CONTAINER = FREEPDB1;

-- ------------------------------------------------------- schema owner
CREATE USER meridian IDENTIFIED BY "MeridianLegacy#2003"
  DEFAULT TABLESPACE users
  QUOTA UNLIMITED ON users;

GRANT CREATE SESSION            TO meridian;
GRANT CREATE TABLE              TO meridian;
GRANT CREATE SEQUENCE           TO meridian;
GRANT CREATE TRIGGER            TO meridian;
GRANT CREATE PROCEDURE          TO meridian;
GRANT CREATE VIEW               TO meridian;
GRANT CREATE MATERIALIZED VIEW  TO meridian;
GRANT UNLIMITED TABLESPACE      TO meridian;

-- --------------------------------------- read-only user for the agent
CREATE USER migration_reader IDENTIFIED BY "ReadOnly#2026";
GRANT CREATE SESSION TO migration_reader;

-- Dictionary access so oracle_describe_schema / oracle_get_ddl work.
GRANT SELECT_CATALOG_ROLE TO migration_reader;
GRANT SELECT ANY DICTIONARY TO migration_reader;
GRANT EXECUTE ON DBMS_METADATA TO migration_reader;

-- NOTE: object-level SELECT grants are issued at the end of
-- 05_seed_data.sql, after the tables exist.
