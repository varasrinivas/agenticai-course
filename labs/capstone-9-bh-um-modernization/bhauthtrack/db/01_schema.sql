-- =====================================================================
-- BHAuthTrack 4.2 -- Oracle 11g schema
-- Bridgeway Behavioral Health, carve-out utilization management
--
-- HISTORY: this file is a RECONSTRUCTION. The original DDL was applied
-- by hand, release by release, and the only record of what changed is
-- schema_changes.txt. Production has drifted from this file at least
-- twice (see BHA-2291, BHA-3104 in that log). Trust the log, not this
-- header comment.
--
-- ALL DATA IN 02_seed.sql IS SYNTHETIC. No real member ever appears.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Members.
--
-- NOTE (BHA-1180, 2012): MEMBER_ID is the BRIDGEWAY carve-out
-- identifier, not the health plan's. The plan's identifier is
-- PLAN_MEMBER_ID and it is nullable because the eligibility feed did
-- not carry it until 2014. Roughly a third of pre-2014 rows still have
-- it NULL. Joining anything to MEMBER_ID and calling it "the member"
-- is the single most common mistake new developers make here.
-- ---------------------------------------------------------------------
CREATE TABLE BH_MEMBER (
    MEMBER_ID          VARCHAR2(24)  NOT NULL,
    PLAN_MEMBER_ID     VARCHAR2(24),
    LAST_NAME          VARCHAR2(60)  NOT NULL,
    FIRST_NAME         VARCHAR2(60)  NOT NULL,
    DOB                DATE          NOT NULL,
    LINE_OF_BUSINESS   VARCHAR2(20)  NOT NULL,
    ELIGIBILITY_START  DATE          NOT NULL,
    ELIGIBILITY_END    DATE,
    CONSTRAINT PK_BH_MEMBER PRIMARY KEY (MEMBER_ID),
    CONSTRAINT CK_BH_MEMBER_LOB CHECK (LINE_OF_BUSINESS IN
        ('COMMERCIAL','MEDICARE_ADV','MANAGED_MEDICAID'))
);
CREATE INDEX IX_BH_MEMBER_PLAN ON BH_MEMBER (PLAN_MEMBER_ID);

-- ---------------------------------------------------------------------
-- Providers. NPI is the national identifier; BRIDGEWAY_PROV_ID is ours.
-- IS_PART2_PROGRAM marks a federally assisted substance-use-disorder
-- treatment program. Records originating from one of these carry
-- redisclosure restrictions that ordinary records do not.
-- ---------------------------------------------------------------------
CREATE TABLE BH_PROVIDER (
    BRIDGEWAY_PROV_ID  VARCHAR2(24)  NOT NULL,
    NPI                CHAR(10)      NOT NULL,
    PROVIDER_NAME      VARCHAR2(120) NOT NULL,
    NETWORK_STATUS     VARCHAR2(16)  NOT NULL,
    IS_PART2_PROGRAM   CHAR(1)       DEFAULT 'N' NOT NULL,
    CONSTRAINT PK_BH_PROVIDER PRIMARY KEY (BRIDGEWAY_PROV_ID),
    CONSTRAINT CK_BH_PROV_NET CHECK (NETWORK_STATUS IN ('IN','OUT','TERMED')),
    CONSTRAINT CK_BH_PROV_P2  CHECK (IS_PART2_PROGRAM IN ('Y','N'))
);

-- ---------------------------------------------------------------------
-- The authorization itself.
--
-- CLINICAL_NARRATIVE is the free-text clinical justification the
-- requesting clinician submits. It is the evidence a reviewer actually
-- reads. When the requesting provider is a Part 2 program, this column
-- holds federally protected substance-use-disorder treatment content.
-- ---------------------------------------------------------------------
CREATE TABLE BH_AUTH (
    AUTH_ID              NUMBER(12)     NOT NULL,
    MEMBER_ID            VARCHAR2(24)   NOT NULL,
    BRIDGEWAY_PROV_ID    VARCHAR2(24)   NOT NULL,
    SERVICE_CODE         VARCHAR2(10)   NOT NULL,   -- CPT or HCPCS
    DIAGNOSIS_CODE       VARCHAR2(10)   NOT NULL,   -- ICD-10
    REQUESTED_LOC        VARCHAR2(8)    NOT NULL,   -- ASAM level, e.g. '3.5'
    REQUESTED_UNITS      NUMBER(5)      NOT NULL,   -- days or sessions
    CLINICAL_NARRATIVE   CLOB,
    STATUS               VARCHAR2(20)   NOT NULL,
    URGENCY              VARCHAR2(12)   DEFAULT 'STANDARD' NOT NULL,
    LEGACY_OVERRIDE      CHAR(1)        DEFAULT 'N' NOT NULL,
    SUBMITTED_TS         DATE           NOT NULL,
    DECIDED_TS           DATE,
    DECIDED_BY           VARCHAR2(40),
    DENIAL_REASON_CODE   VARCHAR2(16),
    CONSTRAINT PK_BH_AUTH PRIMARY KEY (AUTH_ID),
    CONSTRAINT FK_BH_AUTH_MEMBER FOREIGN KEY (MEMBER_ID)
        REFERENCES BH_MEMBER (MEMBER_ID),
    CONSTRAINT FK_BH_AUTH_PROV FOREIGN KEY (BRIDGEWAY_PROV_ID)
        REFERENCES BH_PROVIDER (BRIDGEWAY_PROV_ID),
    CONSTRAINT CK_BH_AUTH_STATUS CHECK (STATUS IN
        ('SUBMITTED','IN_REVIEW','PENDED','APPROVED','DENIED','EXPIRED')),
    CONSTRAINT CK_BH_AUTH_URGENCY CHECK (URGENCY IN ('STANDARD','EXPEDITED'))
);
CREATE INDEX IX_BH_AUTH_MEMBER ON BH_AUTH (MEMBER_ID);
CREATE INDEX IX_BH_AUTH_STATUS ON BH_AUTH (STATUS);

CREATE SEQUENCE SEQ_BH_AUTH_ID START WITH 500000 INCREMENT BY 1 NOCACHE;

-- ---------------------------------------------------------------------
-- Concurrent review. THIS TABLE IS THE WHOLE POINT OF BEHAVIORAL HEALTH
-- UTILIZATION MANAGEMENT and it has no analogue in medical prior auth.
--
-- An authorization is not one decision. It is an initial decision plus
-- a series of continued-stay reviews on a cadence set by level of care.
-- NEXT_REVIEW_DUE is a regulatory deadline, not a reminder.
-- ---------------------------------------------------------------------
CREATE TABLE BH_LOC_REVIEW (
    REVIEW_ID            NUMBER(12)     NOT NULL,
    AUTH_ID              NUMBER(12)     NOT NULL,
    REVIEW_SEQ           NUMBER(3)      NOT NULL,   -- 1 = initial, 2..n = continued stay
    REVIEWED_LOC         VARCHAR2(8)    NOT NULL,
    APPROVED_UNITS       NUMBER(5)      NOT NULL,
    REVIEW_INTERVAL_DAYS NUMBER(3)      NOT NULL,
    NEXT_REVIEW_DUE      DATE,
    OUTCOME              VARCHAR2(20)   NOT NULL,
    REVIEWER_USER_ID     VARCHAR2(40)   NOT NULL,
    REVIEWER_CREDENTIAL  VARCHAR2(20)   NOT NULL,   -- 'RN', 'LCSW', 'MD', 'MD_PSYCH', 'MD_ADDICTION'
    REVIEW_TS            DATE           NOT NULL,
    CONSTRAINT PK_BH_LOC_REVIEW PRIMARY KEY (REVIEW_ID),
    CONSTRAINT FK_BH_LOCREV_AUTH FOREIGN KEY (AUTH_ID)
        REFERENCES BH_AUTH (AUTH_ID),
    CONSTRAINT UQ_BH_LOCREV_SEQ UNIQUE (AUTH_ID, REVIEW_SEQ),
    CONSTRAINT CK_BH_LOCREV_OUTCOME CHECK (OUTCOME IN
        ('APPROVED','PENDED','DENIED','STEPPED_DOWN','DISCHARGED'))
);

CREATE SEQUENCE SEQ_BH_REVIEW_ID START WITH 900000 INCREMENT BY 1 NOCACHE;

-- ---------------------------------------------------------------------
-- Standardised instrument scores feeding the level-of-care rules.
-- ---------------------------------------------------------------------
CREATE TABLE BH_ASSESSMENT (
    ASSESSMENT_ID    NUMBER(12)   NOT NULL,
    AUTH_ID          NUMBER(12)   NOT NULL,
    INSTRUMENT       VARCHAR2(16) NOT NULL,   -- 'PHQ9','GAD7','CSSRS','ASAM_DIM'
    DIMENSION        NUMBER(1),               -- 1..6, ASAM dimensions only
    SCORE            NUMBER(3)    NOT NULL,
    ASSESSED_TS      DATE         NOT NULL,
    CONSTRAINT PK_BH_ASSESSMENT PRIMARY KEY (ASSESSMENT_ID),
    CONSTRAINT FK_BH_ASSESS_AUTH FOREIGN KEY (AUTH_ID)
        REFERENCES BH_AUTH (AUTH_ID),
    CONSTRAINT CK_BH_ASSESS_INSTR CHECK (INSTRUMENT IN
        ('PHQ9','GAD7','CSSRS','ASAM_DIM')),
    CONSTRAINT CK_BH_ASSESS_DIM CHECK (DIMENSION BETWEEN 1 AND 6)
);

CREATE SEQUENCE SEQ_BH_ASSESS_ID START WITH 700000 INCREMENT BY 1 NOCACHE;

-- ---------------------------------------------------------------------
-- 42 CFR Part 2 consent.
--
-- A Part 2 consent is NOT a blanket release. It names the specific
-- recipient, states the purpose, and expires. Disclosing protected
-- content to a party this table does not name for that purpose is the
-- violation. There is no "minimum necessary" shortcut here the way
-- there is under HIPAA.
--
-- REDISCLOSURE_NOTICE_SENT records that the required notice
-- accompanied the disclosure.
-- ---------------------------------------------------------------------
CREATE TABLE BH_CONSENT (
    CONSENT_ID                NUMBER(12)    NOT NULL,
    AUTH_ID                   NUMBER(12)    NOT NULL,
    MEMBER_ID                 VARCHAR2(24)  NOT NULL,
    RECIPIENT_NAME            VARCHAR2(120) NOT NULL,
    RECIPIENT_TYPE            VARCHAR2(24)  NOT NULL,
    PURPOSE                   VARCHAR2(200) NOT NULL,
    SCOPE                     VARCHAR2(24)  NOT NULL,
    SIGNED_TS                 DATE          NOT NULL,
    EXPIRES_TS                DATE          NOT NULL,
    REVOKED_TS                DATE,
    REDISCLOSURE_NOTICE_SENT  CHAR(1)       DEFAULT 'N' NOT NULL,
    CONSTRAINT PK_BH_CONSENT PRIMARY KEY (CONSENT_ID),
    CONSTRAINT FK_BH_CONSENT_AUTH FOREIGN KEY (AUTH_ID)
        REFERENCES BH_AUTH (AUTH_ID),
    CONSTRAINT FK_BH_CONSENT_MEMBER FOREIGN KEY (MEMBER_ID)
        REFERENCES BH_MEMBER (MEMBER_ID),
    CONSTRAINT CK_BH_CONSENT_SCOPE CHECK (SCOPE IN
        ('FULL_RECORD','AUTH_DECISION_ONLY','DATES_OF_SERVICE_ONLY')),
    CONSTRAINT CK_BH_CONSENT_NOTICE CHECK (REDISCLOSURE_NOTICE_SENT IN ('Y','N'))
);

CREATE SEQUENCE SEQ_BH_CONSENT_ID START WITH 800000 INCREMENT BY 1 NOCACHE;

-- ---------------------------------------------------------------------
-- The "queue". There is no message broker in this system. A row lands
-- here and poll_queue.sh, running from cron every five minutes, picks
-- it up. If the process dies mid-batch the row stays LOCKED and a human
-- clears it on Monday. See ops/README for the runbook nobody follows.
-- ---------------------------------------------------------------------
CREATE TABLE BH_AUTH_QUEUE (
    QUEUE_ID      NUMBER(12)    NOT NULL,
    AUTH_ID       NUMBER(12)    NOT NULL,
    EVENT_TYPE    VARCHAR2(32)  NOT NULL,
    PAYLOAD       VARCHAR2(4000),
    STATE         VARCHAR2(12)  DEFAULT 'NEW' NOT NULL,
    LOCKED_BY     VARCHAR2(40),
    ENQUEUED_TS   DATE          NOT NULL,
    PROCESSED_TS  DATE,
    CONSTRAINT PK_BH_AUTH_QUEUE PRIMARY KEY (QUEUE_ID),
    CONSTRAINT FK_BH_QUEUE_AUTH FOREIGN KEY (AUTH_ID)
        REFERENCES BH_AUTH (AUTH_ID),
    CONSTRAINT CK_BH_QUEUE_STATE CHECK (STATE IN ('NEW','LOCKED','DONE','FAILED'))
);

CREATE SEQUENCE SEQ_BH_QUEUE_ID START WITH 100000 INCREMENT BY 1 NOCACHE;

-- ---------------------------------------------------------------------
-- Audit.
--
-- Written by TRG_BH_AUTH_AUDIT below. Note what it captures: the OLD
-- and NEW clinical narrative, in full, on every update. That was a
-- 2012 decision made so the appeals team could see what the clinician
-- originally wrote. Nobody has revisited whether an audit table is an
-- appropriate place for federally protected treatment content.
-- ---------------------------------------------------------------------
CREATE TABLE BH_AUDIT_LOG (
    AUDIT_ID        NUMBER(12)     NOT NULL,
    AUTH_ID         NUMBER(12)     NOT NULL,
    ACTION          VARCHAR2(32)   NOT NULL,
    ACTOR_USER_ID   VARCHAR2(40)   NOT NULL,
    ACTOR_ROLE_MASK NUMBER(6)      NOT NULL,
    OLD_STATUS      VARCHAR2(20),
    NEW_STATUS      VARCHAR2(20),
    OLD_NARRATIVE   CLOB,
    NEW_NARRATIVE   CLOB,
    ACTION_TS       DATE           NOT NULL,
    CONSTRAINT PK_BH_AUDIT_LOG PRIMARY KEY (AUDIT_ID),
    CONSTRAINT FK_BH_AUDIT_AUTH FOREIGN KEY (AUTH_ID)
        REFERENCES BH_AUTH (AUTH_ID)
);

CREATE SEQUENCE SEQ_BH_AUDIT_ID START WITH 1 INCREMENT BY 1 NOCACHE;

-- ---------------------------------------------------------------------
-- Authorization. ROLE_MASK is a bitmask:
--     1  BH_INTAKE        may create and edit an authorization
--     2  BH_NURSE         may review and APPROVE -- never deny
--     4  BH_MD            may issue an adverse determination
--     8  BH_MD_PSYCH      psychiatric peer reviewer
--    16  BH_MD_ADDICTION  addiction-medicine peer reviewer
--    32  BH_ADMIN         user administration, consent administration
--
-- The nurse/MD split is not a convenience. A nurse may approve but may
-- never deny; only a physician may issue an adverse determination. For
-- substance-use and psychiatric level-of-care denials the reviewer is
-- expected to be same-specialty, which is why 8 and 16 exist
-- separately from 4.
-- ---------------------------------------------------------------------
CREATE TABLE BH_USER_ROLE (
    USER_ID     VARCHAR2(40) NOT NULL,
    ROLE_MASK   NUMBER(6)    NOT NULL,
    LDAP_DN     VARCHAR2(200) NOT NULL,
    ACTIVE_FLAG CHAR(1)      DEFAULT 'Y' NOT NULL,
    CONSTRAINT PK_BH_USER_ROLE PRIMARY KEY (USER_ID),
    CONSTRAINT CK_BH_USER_ACTIVE CHECK (ACTIVE_FLAG IN ('Y','N'))
);

-- ---------------------------------------------------------------------
-- The audit trigger. Fires on every update to BH_AUTH.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TRIGGER TRG_BH_AUTH_AUDIT
AFTER UPDATE ON BH_AUTH
FOR EACH ROW
DECLARE
    v_actor  VARCHAR2(40);
    v_mask   NUMBER(6);
BEGIN
    v_actor := NVL(SYS_CONTEXT('BHAUTH_CTX','USER_ID'), USER);
    BEGIN
        SELECT ROLE_MASK INTO v_mask FROM BH_USER_ROLE WHERE USER_ID = v_actor;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN v_mask := 0;
    END;

    INSERT INTO BH_AUDIT_LOG (
        AUDIT_ID, AUTH_ID, ACTION, ACTOR_USER_ID, ACTOR_ROLE_MASK,
        OLD_STATUS, NEW_STATUS, OLD_NARRATIVE, NEW_NARRATIVE, ACTION_TS
    ) VALUES (
        SEQ_BH_AUDIT_ID.NEXTVAL, :NEW.AUTH_ID, 'UPDATE', v_actor, v_mask,
        :OLD.STATUS, :NEW.STATUS,
        :OLD.CLINICAL_NARRATIVE,   -- full protected narrative, every update
        :NEW.CLINICAL_NARRATIVE,
        SYSDATE
    );
END;
/

-- ---------------------------------------------------------------------
-- Reporting view. Crystal Reports binds to these column names
-- positionally. Renaming a column here silently breaks eleven reports
-- that live on a share drive and are not in source control.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_BH_AUTH_SUMMARY AS
SELECT a.AUTH_ID,
       a.MEMBER_ID,
       m.PLAN_MEMBER_ID,
       a.SERVICE_CODE,
       a.DIAGNOSIS_CODE,
       a.REQUESTED_LOC,
       a.STATUS,
       a.URGENCY,
       p.IS_PART2_PROGRAM,
       a.SUBMITTED_TS,
       a.DECIDED_TS
  FROM BH_AUTH a
  JOIN BH_MEMBER   m ON m.MEMBER_ID = a.MEMBER_ID
  JOIN BH_PROVIDER p ON p.BRIDGEWAY_PROV_ID = a.BRIDGEWAY_PROV_ID;
