-- =====================================================================
-- Meridian Public Records -- legacy UCC filing system
-- Oracle 11g-era DDL, still running on Oracle Free 23c.
--
-- Every object here contains at least one construct that does NOT
-- translate cleanly to PostgreSQL. That is deliberate. See
-- spec/agent-spec.md for the full Oracle-ism registry.
-- =====================================================================

ALTER SESSION SET CURRENT_SCHEMA = MERIDIAN;

-- ---------------------------------------------------------------------
-- STATE_SOS_SOURCE
-- Traps: TIMESTAMP WITH LOCAL TIME ZONE (session-relative!), and a
--        NUMBER column with no precision at all.
-- ---------------------------------------------------------------------
CREATE TABLE state_sos_source (
  state_code        CHAR(2)                            NOT NULL,
  state_name        VARCHAR2(60 BYTE)                  NOT NULL,
  feed_format       VARCHAR2(20 BYTE)                  NOT NULL,
  last_sync         TIMESTAMP WITH LOCAL TIME ZONE,
  records_expected  NUMBER,                            -- no precision, no scale
  is_active         CHAR(1) DEFAULT 'Y'                NOT NULL,
  CONSTRAINT pk_state_sos_source PRIMARY KEY (state_code),
  CONSTRAINT ck_sos_active CHECK (is_active IN ('Y','N'))
);

-- ---------------------------------------------------------------------
-- UCC_FILING
-- Traps: NUMBER(12) identity fed by a sequence + BEFORE INSERT trigger;
--        FILED_DATE / LAPSE_DATE are Oracle DATE, which carries a TIME
--        component -- mapping them to PostgreSQL `date` silently
--        truncates 14:32:07 to midnight and changes which filings look
--        lapsed. COLLATERAL_DESC is a CLOB.
-- ---------------------------------------------------------------------
CREATE TABLE ucc_filing (
  filing_id         NUMBER(12)                         NOT NULL,
  filing_number     VARCHAR2(20 BYTE)                  NOT NULL,
  state_code        CHAR(2)                            NOT NULL,
  filing_type       VARCHAR2(12 BYTE)                  NOT NULL,
  filed_date        DATE                               NOT NULL,
  lapse_date        DATE,
  status            VARCHAR2(12 BYTE) DEFAULT 'ACTIVE' NOT NULL,
  collateral_desc   CLOB,
  page_count        NUMBER(4,0),
  filing_fee        NUMBER(9,2),
  created_by        VARCHAR2(30 BYTE) DEFAULT USER     NOT NULL,
  created_ts        DATE DEFAULT SYSDATE               NOT NULL,
  CONSTRAINT pk_ucc_filing PRIMARY KEY (filing_id),
  CONSTRAINT uq_ucc_filing_number UNIQUE (filing_number),
  CONSTRAINT fk_filing_state FOREIGN KEY (state_code)
    REFERENCES state_sos_source (state_code),
  CONSTRAINT ck_filing_type CHECK (filing_type IN
    ('UCC1','UCC3_AMD','UCC3_CONT','UCC3_TERM','UCC5')),
  CONSTRAINT ck_filing_status CHECK (status IN ('ACTIVE','TERMINATED','LAPSED'))
);

CREATE INDEX ix_filing_state_date ON ucc_filing (state_code, filed_date);
CREATE INDEX ix_filing_lapse ON ucc_filing (lapse_date);
-- Function-based index -- PostgreSQL supports these but the syntax differs.
CREATE INDEX ix_filing_upper_number ON ucc_filing (UPPER(filing_number));

-- ---------------------------------------------------------------------
-- UCC_DEBTOR
-- THE PLANTED BUG LIVES HERE.
-- MAILING_ADDRESS_2 is populated with '' for roughly 1,400 rows. Oracle
-- stores '' as NULL. PostgreSQL stores it as a zero-length string. A
-- naive CSV round-trip turns those Oracle NULLs into PostgreSQL empty
-- strings, and every `IS NULL` predicate in the application silently
-- starts returning fewer rows. The migration-validator must catch this.
-- ---------------------------------------------------------------------
CREATE TABLE ucc_debtor (
  debtor_id         NUMBER(12)                         NOT NULL,
  filing_id         NUMBER(12)                         NOT NULL,
  debtor_name       VARCHAR2(240 BYTE)                 NOT NULL,
  debtor_type       VARCHAR2(12 BYTE)                  NOT NULL,
  mailing_address_1 VARCHAR2(120 BYTE),
  mailing_address_2 VARCHAR2(120 BYTE),   -- <-- the empty-string trap
  city              VARCHAR2(60 BYTE),
  state_code        CHAR(2),
  postal_code       VARCHAR2(10 BYTE),
  CONSTRAINT pk_ucc_debtor PRIMARY KEY (debtor_id),
  CONSTRAINT fk_debtor_filing FOREIGN KEY (filing_id)
    REFERENCES ucc_filing (filing_id) ON DELETE CASCADE,
  CONSTRAINT ck_debtor_type CHECK (debtor_type IN ('ORGANIZATION','INDIVIDUAL'))
);

CREATE INDEX ix_debtor_name ON ucc_debtor (debtor_name);
CREATE INDEX ix_debtor_filing ON ucc_debtor (filing_id);

-- ---------------------------------------------------------------------
-- UCC_SECURED_PARTY
-- Traps: TAX_ID is RAW(16) -- a 16-byte binary blob that is really a
--        UUID. Maps to PostgreSQL `uuid`, not `bytea`, if you look at
--        the data. VARCHAR2(60 BYTE) vs CHAR length semantics matter
--        for any name containing multibyte characters.
-- ---------------------------------------------------------------------
CREATE TABLE ucc_secured_party (
  secured_party_id  NUMBER(12)                         NOT NULL,
  filing_id         NUMBER(12)                         NOT NULL,
  party_name        VARCHAR2(240 BYTE)                 NOT NULL,
  tax_id            RAW(16),
  contact_email     VARCHAR2(120 BYTE),
  is_assignee       CHAR(1) DEFAULT 'N'                NOT NULL,
  CONSTRAINT pk_ucc_secured_party PRIMARY KEY (secured_party_id),
  CONSTRAINT fk_sp_filing FOREIGN KEY (filing_id)
    REFERENCES ucc_filing (filing_id) ON DELETE CASCADE,
  CONSTRAINT ck_sp_assignee CHECK (is_assignee IN ('Y','N'))
);

CREATE INDEX ix_sp_filing ON ucc_secured_party (filing_id);
CREATE INDEX ix_sp_name ON ucc_secured_party (party_name);

-- ---------------------------------------------------------------------
-- UCC_AMENDMENT
-- Trap: self-referencing PARENT_AMENDMENT_ID. The application walks it
--       with CONNECT BY PRIOR, which has no PostgreSQL equivalent --
--       it becomes WITH RECURSIVE, and the ordering semantics differ.
-- ---------------------------------------------------------------------
CREATE TABLE ucc_amendment (
  amendment_id        NUMBER(12)                       NOT NULL,
  filing_id           NUMBER(12)                       NOT NULL,
  parent_amendment_id NUMBER(12),
  amendment_type      VARCHAR2(12 BYTE)                NOT NULL,
  amendment_date      DATE                             NOT NULL,
  notes               VARCHAR2(400 BYTE),
  CONSTRAINT pk_ucc_amendment PRIMARY KEY (amendment_id),
  CONSTRAINT fk_amd_filing FOREIGN KEY (filing_id)
    REFERENCES ucc_filing (filing_id) ON DELETE CASCADE,
  CONSTRAINT fk_amd_parent FOREIGN KEY (parent_amendment_id)
    REFERENCES ucc_amendment (amendment_id),
  CONSTRAINT ck_amd_type CHECK (amendment_type IN
    ('AMENDMENT','CONTINUATION','TERMINATION','ASSIGNMENT'))
);

CREATE INDEX ix_amd_parent ON ucc_amendment (parent_amendment_id);

-- ---------------------------------------------------------------------
-- FILING_AUDIT
-- Traps: DOC_IMAGE is a BLOB. Rows are written by an AUTONOMOUS
--        TRANSACTION procedure (see 03_packages.sql) so audit rows
--        survive a rollback of the business transaction. PostgreSQL has
--        no autonomous transactions -- this needs a design change, and
--        the plsql-converter subagent must REFUSE to convert it rather
--        than quietly dropping the pragma.
-- ---------------------------------------------------------------------
CREATE TABLE filing_audit (
  audit_id      NUMBER(12)                             NOT NULL,
  filing_id     NUMBER(12),
  action        VARCHAR2(20 BYTE)                      NOT NULL,
  action_ts     TIMESTAMP(6) DEFAULT SYSTIMESTAMP      NOT NULL,
  actor         VARCHAR2(30 BYTE) DEFAULT USER         NOT NULL,
  doc_image     BLOB,
  detail        CLOB,
  CONSTRAINT pk_filing_audit PRIMARY KEY (audit_id)
);

CREATE INDEX ix_audit_filing ON filing_audit (filing_id);
