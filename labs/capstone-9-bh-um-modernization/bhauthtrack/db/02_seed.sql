-- =====================================================================
-- BHAuthTrack 4.2 -- seed data
--
-- ***  EVERY ROW IN THIS FILE IS SYNTHETIC.  ***
--
-- Generated from documented seed 20260822. No real member, provider,
-- clinician or clinical narrative appears anywhere. The names are drawn
-- from a fictional-name list; the addresses and NPIs are structurally
-- valid and belong to nobody. Service, diagnosis and ASAM codes ARE
-- real and correctly formatted -- the codes have to be right for the
-- rules to be worth reading. The people do not exist.
--
-- This matters beyond good manners. The agent that reads this codebase
-- operates under a hard "no PHI in prompts, ever" constraint enforced
-- by a PreToolUse hook. These synthetic fixtures are what make it
-- possible to point an agent at this system at all.
--
-- ---------------------------------------------------------------------
-- WHAT THIS FILE IS FOR
--
-- It is not a demo dataset. Each authorization below exercises one
-- specific branch of PKG_LOC_RULES.EVAL_LOC, and the expected outcome
-- is stated in a comment above it. Together they are the golden set the
-- parity validator runs through both the legacy ladder and whatever
-- decision table replaces it.
--
-- If a modernized engine disagrees with any expected outcome here, that
-- disagreement is the finding.
--
-- The expected outcomes below were verified by walking the branches of
-- PKG_LOC_RULES.EVAL_LOC over these exact rows. Where a case also has a
-- BH_LOC_REVIEW sequence 1, that row records the same level, units and
-- interval the ladder produces -- so the fixture is internally
-- consistent and a divergence in a port is a real divergence, not a
-- seeding error.
--
-- EXACTLY ONE case triggers the branch 7 overlap: 500001.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Two tables the application reads that were never part of a release.
-- In production they live in other teams' schemas behind synonyms; see
-- schema_changes.txt, "TABLES THIS FILE DOES NOT COVER". They are
-- created here so the fixture is self-contained and runnable.
-- ---------------------------------------------------------------------
CREATE TABLE BH_BENEFIT_ACCUM (
    MEMBER_ID       VARCHAR2(24) NOT NULL,
    LOC_CATEGORY    VARCHAR2(20) NOT NULL,
    BENEFIT_YEAR    CHAR(4)      NOT NULL,
    REMAINING_DAYS  NUMBER(4)    NOT NULL
);

CREATE TABLE BH_FACILITY_CAPACITY (
    BRIDGEWAY_PROV_ID VARCHAR2(24) NOT NULL,
    LOC_LEVEL         VARCHAR2(8)  NOT NULL,
    OPEN_BEDS         NUMBER(4)    NOT NULL,
    AS_OF             DATE         NOT NULL
);


-- =====================================================================
-- MEMBERS
--
-- Ten members. THREE have PLAN_MEMBER_ID NULL -- 31%, matching the
-- production figure recorded under BHA-1180. Those three were enrolled
-- before the 2014 eligibility feed rewrite and cannot be joined to the
-- health plan at all.
--
-- Note the identifier formats. Bridgeway's key is BW-nnnnnnn. The
-- plan's is a nine-digit string. They are NOT interchangeable, and the
-- modern platform's opaque member_id VARCHAR(32) will accept either
-- without objecting -- which is why a 1:1 port matches by luck.
-- =====================================================================
INSERT INTO BH_MEMBER VALUES ('BW-1000401','483920117','Aldricht','Marisol',  DATE '1988-04-17','COMMERCIAL',      DATE '2015-01-01', NULL);
INSERT INTO BH_MEMBER VALUES ('BW-1000402','483920244','Brennecke','Tobias',  DATE '1979-11-02','COMMERCIAL',      DATE '2016-06-01', NULL);
INSERT INTO BH_MEMBER VALUES ('BW-1000403','483920388','Calloway-Reid','June',DATE '2001-02-25','MANAGED_MEDICAID',DATE '2019-03-15', NULL);
-- The three pre-2014 enrolments with no plan identifier. -----------------
INSERT INTO BH_MEMBER VALUES ('BW-1000404', NULL,      'Deshotel','Amara',    DATE '1972-08-09','COMMERCIAL',      DATE '2011-05-01', NULL);
INSERT INTO BH_MEMBER VALUES ('BW-1000405', NULL,      'Erlichman','Peter',   DATE '1965-01-30','MEDICARE_ADV',    DATE '2012-09-01', NULL);
INSERT INTO BH_MEMBER VALUES ('BW-1000406', NULL,      'Fontanez','Ruby',     DATE '1994-06-14','MANAGED_MEDICAID',DATE '2013-02-01', NULL);
-- ------------------------------------------------------------------------
INSERT INTO BH_MEMBER VALUES ('BW-1000407','483920512','Grantham','Odile',    DATE '1983-12-05','COMMERCIAL',      DATE '2017-01-01', NULL);
INSERT INTO BH_MEMBER VALUES ('BW-1000408','483920655','Halvorsen','Nils',    DATE '1990-09-22','COMMERCIAL',      DATE '2018-07-01', NULL);
INSERT INTO BH_MEMBER VALUES ('BW-1000409','483920701','Ibarra-Quinn','Sol',  DATE '2004-03-11','MANAGED_MEDICAID',DATE '2020-01-01', NULL);
-- Deliberate duplicate plan identifier: twins, matched by the 2014
-- backfill on name and date of birth. MemberDao.findByPlanMemberId()
-- returns a LIST for exactly this reason, and SearchController shows
-- only the first.
INSERT INTO BH_MEMBER VALUES ('BW-1000410','483920701','Ibarra-Quinn','Wren', DATE '2004-03-11','MANAGED_MEDICAID',DATE '2020-01-01', NULL);


-- =====================================================================
-- PROVIDERS
--
-- Three are Part 2 programs (federally assisted SUD treatment). One is
-- TERMED and one is OUT of network -- both are needed to exercise
-- branch 1 of the ladder.
--
-- IS_PART2_PROGRAM was backfilled from a spreadsheet in 2014 and has
-- never been audited. Treat it as an input, not as ground truth.
-- =====================================================================
INSERT INTO BH_PROVIDER VALUES ('BWP-2001','1548893027','Northgate Recovery Center',        'IN',    'Y');
INSERT INTO BH_PROVIDER VALUES ('BWP-2002','1730054918','Harbor Ridge Behavioral Hospital', 'IN',    'N');
INSERT INTO BH_PROVIDER VALUES ('BWP-2003','1992217640','Cedar Line Withdrawal Management', 'IN',    'Y');
INSERT INTO BH_PROVIDER VALUES ('BWP-2004','1226770359','Willowbrook Counseling Associates','IN',    'N');
INSERT INTO BH_PROVIDER VALUES ('BWP-2005','1884016273','Tallgrass Residential SUD Program','OUT',   'Y');
INSERT INTO BH_PROVIDER VALUES ('BWP-2006','1665328104','Meridian Day Treatment',           'TERMED','N');


-- =====================================================================
-- USERS
--
-- ROLE_MASK is a bitmask: 1 intake, 2 nurse, 4 MD, 8 psych peer,
-- 16 addiction-medicine peer, 32 admin.
--
-- Read the masks carefully; they are the fixture for the authorization
-- findings:
--   rknowles  2   nurse. May approve. May NEVER deny.
--   pvasquez  4   physician. May deny -- but NOT a SUD denial (needs 16).
--   tokafor  20   4|16, addiction medicine. May deny an F1x case.
--   dmirembe 12   4|8,  psychiatric. May deny F2x-F4x, not F1x.
--   sbanerji 33   1|32, intake + admin. Mask 33 is >= 4, so the JSTL
--                 guards in decision.jsp SHOW this user the deny button
--                 while UserContext.hasRole(ROLE_MD) refuses it. That
--                 is the numeric-vs-bitwise divergence, seeded.
--   bhauth_ws 0   the SOAP service account. Reaches the decision path
--                 with no roles and credential UNKNOWN.
-- =====================================================================
INSERT INTO BH_USER_ROLE VALUES ('rknowles',  2, 'uid=rknowles,ou=people,dc=bridgeway,dc=internal', 'Y');
INSERT INTO BH_USER_ROLE VALUES ('pvasquez',  4, 'uid=pvasquez,ou=people,dc=bridgeway,dc=internal', 'Y');
INSERT INTO BH_USER_ROLE VALUES ('tokafor',  20, 'uid=tokafor,ou=people,dc=bridgeway,dc=internal',  'Y');
INSERT INTO BH_USER_ROLE VALUES ('dmirembe', 12, 'uid=dmirembe,ou=people,dc=bridgeway,dc=internal', 'Y');
INSERT INTO BH_USER_ROLE VALUES ('sbanerji', 33, 'uid=sbanerji,ou=people,dc=bridgeway,dc=internal', 'Y');
INSERT INTO BH_USER_ROLE VALUES ('lmoreau',   1, 'uid=lmoreau,ou=people,dc=bridgeway,dc=internal',  'Y');
INSERT INTO BH_USER_ROLE VALUES ('bhauth_ws', 0, 'uid=bhauth_ws,ou=svc,dc=bridgeway,dc=internal',   'Y');


-- =====================================================================
-- BENEFIT ACCUMULATORS AND BED CAPACITY
--
-- Inputs to the Java-side adjustments in LocRulesService. Note that
-- BW-1000407 has ZERO residential days left -- that member's case pends
-- with BENEFIT_EXHAUSTED no matter what the ladder decided.
-- =====================================================================
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000401','RESIDENTIAL','2026', 30);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000401','INPATIENT',  '2026', 30);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000402','RESIDENTIAL','2026', 30);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000403','RESIDENTIAL','2026', 30);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000404','INPATIENT',  '2026', 30);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000405','OUTPATIENT', '2026', 60);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000406','RESIDENTIAL','2026', 30);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000407','RESIDENTIAL','2026',  0);   -- exhausted
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000408','PHP',        '2026', 45);
INSERT INTO BH_BENEFIT_ACCUM VALUES ('BW-1000409','IOP',        '2026', 45);

-- Capacity: 3.7 has open beds, 3.5 does NOT. Any case granted 3.5 by
-- the ladder is stepped down to 3.1 by LocRulesService adjustment C.
INSERT INTO BH_FACILITY_CAPACITY VALUES ('BWP-2002','3.7', 4, DATE '2026-08-17');
INSERT INTO BH_FACILITY_CAPACITY VALUES ('BWP-2001','3.5', 0, DATE '2026-08-17');
INSERT INTO BH_FACILITY_CAPACITY VALUES ('BWP-2003','3.1', 6, DATE '2026-08-17');
INSERT INTO BH_FACILITY_CAPACITY VALUES ('BWP-2005','3.5', 8, DATE '2026-08-17');  -- OUT of network


-- =====================================================================
-- THE GOLDEN SET
--
-- Authorization ids are assigned explicitly rather than from the
-- sequence so the expected outcomes below can name them. Reset the
-- sequence past them before running the application.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 500001 -- *** THE BRANCH 7 OVERLAP. THE CENTRAL FIXTURE. ***
--
-- C-SSRS 4        -> branch 2, +6   (score 6)
-- ASAM dim 1 = 3  -> branch 3, +4   (score 10), falls through
-- dims 2,3 low    -> branch 4, no
-- dims 5,6 low    -> branch 5, no
-- dim 4 = 3       -> branch 6, no
--
-- At branch 7 the score is 10 and dimension 1 is 3.
--   B7a: score >= 10 AND d1 >= 3   -> TRUE
--   B7b: score >= 8                -> ALSO TRUE
--
-- Both fire. The ladder commits on the first, so the answer is 3.7.
--
-- EXPECTED (legacy): APPROVED, 3.7, 10 units, 5-day interval,
--                    rule_path 'B2:cssrs>=4(+6);B3:d1=3(+4);B7a:...'
--
-- Flatten branches 7a and 7b into an unordered decision table and:
--   FIRST     -> 3.7, but only if row order survived the translation
--   UNIQUE    -> ERROR, two rules match
--   PRIORITY  -> whichever output the priority list ranks higher
--   COLLECT   -> both, and the caller has to choose
--
-- The hit policy IS the decision here. There is no neutral choice.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500001,'BW-1000401','BWP-2002','H0019','F33.2','3.7',10,
  'Member presents following a third emergency department contact this quarter. Reports '
||'escalating passive ideation with a specific plan disclosed at triage. Outpatient contact '
||'has been irregular. Requesting medically monitored inpatient care for stabilisation.',
  'IN_REVIEW','STANDARD','N', DATE '2026-08-18', NULL, NULL, NULL);

INSERT INTO BH_ASSESSMENT VALUES (700001,500001,'ASAM_DIM',1,3,DATE '2026-08-18');
INSERT INTO BH_ASSESSMENT VALUES (700002,500001,'ASAM_DIM',2,1,DATE '2026-08-18');
INSERT INTO BH_ASSESSMENT VALUES (700003,500001,'ASAM_DIM',3,2,DATE '2026-08-18');
INSERT INTO BH_ASSESSMENT VALUES (700004,500001,'ASAM_DIM',4,3,DATE '2026-08-18');
INSERT INTO BH_ASSESSMENT VALUES (700005,500001,'ASAM_DIM',5,2,DATE '2026-08-18');
INSERT INTO BH_ASSESSMENT VALUES (700006,500001,'ASAM_DIM',6,2,DATE '2026-08-18');
INSERT INTO BH_ASSESSMENT VALUES (700007,500001,'CSSRS',NULL,4,DATE '2026-08-18');
INSERT INTO BH_CONSENT   VALUES (800001,500001,'BW-1000401','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review and benefit determination','AUTH_DECISION_ONLY',
  DATE '2026-08-18', DATE '2027-08-18', NULL, 'N');


-- ---------------------------------------------------------------------
-- 500002 -- branch 7b, clean. NO overlap: dimension 1 is 0, so B7a
-- cannot fire and only the 3.5 rule matches.
--
-- C-SSRS 4  -> +6  (score 6)
-- dim 5 = 3 -> branch 5 elif, +2 (score 8)
--
-- EXPECTED (legacy ladder): APPROVED, 3.5, 14 units, 7-day interval.
--
-- BUT NOTE THE JAVA LAYER. BWP-2001 has zero open 3.5 beds, so
-- LocRulesService adjustment C steps this down to 3.1 and rewrites the
-- interval to 14 days. The PL/SQL says 3.5. The system says 3.1.
--
-- A port that extracts only PKG_LOC_RULES gets this case wrong, and it
-- gets it wrong SILENTLY -- 3.5 is a plausible answer.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500002,'BW-1000402','BWP-2001','H0018','F10.20','3.5',14,
  'Alcohol use disorder, severe. Two prior withdrawal-management admissions in the past year. '
||'Home environment includes another individual who is actively drinking. Requesting '
||'clinically managed high-intensity residential treatment.',
  'IN_REVIEW','STANDARD','N', DATE '2026-08-19', NULL, NULL, NULL);

INSERT INTO BH_ASSESSMENT VALUES (700011,500002,'ASAM_DIM',1,0,DATE '2026-08-19');
INSERT INTO BH_ASSESSMENT VALUES (700012,500002,'ASAM_DIM',2,1,DATE '2026-08-19');
INSERT INTO BH_ASSESSMENT VALUES (700013,500002,'ASAM_DIM',3,2,DATE '2026-08-19');
INSERT INTO BH_ASSESSMENT VALUES (700014,500002,'ASAM_DIM',4,3,DATE '2026-08-19');
INSERT INTO BH_ASSESSMENT VALUES (700015,500002,'ASAM_DIM',5,3,DATE '2026-08-19');
INSERT INTO BH_ASSESSMENT VALUES (700016,500002,'ASAM_DIM',6,2,DATE '2026-08-19');
INSERT INTO BH_ASSESSMENT VALUES (700017,500002,'CSSRS',NULL,4,DATE '2026-08-19');
-- Part 2 program (BWP-2001) with consent limited to the determination.
-- The narrative above may NOT be disclosed under this consent -- and
-- AuthCaseService puts it in the queue payload and the log line anyway.
INSERT INTO BH_CONSENT   VALUES (800002,500002,'BW-1000402','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review and benefit determination','AUTH_DECISION_ONLY',
  DATE '2026-08-19', DATE '2027-08-19', NULL, 'N');


-- ---------------------------------------------------------------------
-- 500003 -- branch 3 commit. Dimension 1 of 4 or more justifies
-- medically managed inpatient on its own, before anything else is
-- considered.
--
-- EXPECTED: APPROVED, 4.0, 5 units, 3-day interval,
--           rule_path 'B3:d1>=4=>4.0;'
--
-- Note the cadence: three days. That is the tightest continued-stay
-- interval in the system, and the reminder job runs weekdays only.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500003,'BW-1000404','BWP-2003','H0019','F11.20','4.0',5,
  'Opioid use disorder with concurrent benzodiazepine use. Autonomic instability noted on '
||'assessment. Requires medically managed withdrawal.',
  'APPROVED','EXPEDITED','N', DATE '2026-08-20', DATE '2026-08-20', 'pvasquez', NULL);

INSERT INTO BH_ASSESSMENT VALUES (700021,500003,'ASAM_DIM',1,4,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700022,500003,'ASAM_DIM',2,3,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700023,500003,'ASAM_DIM',3,2,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700024,500003,'ASAM_DIM',4,2,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700025,500003,'ASAM_DIM',5,3,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700026,500003,'ASAM_DIM',6,3,DATE '2026-08-20');
INSERT INTO BH_CONSENT   VALUES (800003,500003,'BW-1000404','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-08-20', DATE '2027-08-20', NULL, 'N');

-- The concurrent-review ladder for 500003. THREE rungs: an initial
-- determination at 4.0 and two continued stays, stepping down to 3.7.
-- This is the loop the modern platform's one-shot process cannot express.
INSERT INTO BH_LOC_REVIEW VALUES (900001,500003,1,'4.0',5,3,DATE '2026-08-23','APPROVED',
  'pvasquez','MD',        DATE '2026-08-20');
INSERT INTO BH_LOC_REVIEW VALUES (900002,500003,2,'4.0',3,3,DATE '2026-08-26','APPROVED',
  'rknowles','RN',        DATE '2026-08-23');
-- Sequence 3 is OVERDUE as of the seed date. Nothing escalated it.
INSERT INTO BH_LOC_REVIEW VALUES (900003,500003,3,'3.7',5,5,DATE '2026-08-21','STEPPED_DOWN',
  'tokafor','MD_ADDICTION',DATE '2026-08-16');


-- ---------------------------------------------------------------------
-- 500004 -- *** LEGACY_OVERRIDE. THE DEAD END. ***
--
-- Branch 0 fires before anything else is read. The dimension scores
-- below are never evaluated; they are present so it is visible that
-- they WOULD have produced 3.5 had the override not short-circuited.
--
-- EXPECTED: PENDED, granted_loc = requested, 0 units,
--           reason_code 'LEGACY_OVR', rule_path 'B0:override'
--
-- AuthStatusService.advance() then handles LEGACY_OVR again, in its own
-- way, in two places.
--
-- BHA-2291, February 2013, ticket body in full: "per DM request".
-- Roughly 400 live rows carry it. Nobody at Bridgeway can say what it
-- means.
--
-- *** THIS BELONGS IN THE MANUAL-REVIEW QUEUE, NOT IN A DECISION TABLE. ***
-- A modernization that reports 100% automated coverage has guessed.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500004,'BW-1000405','BWP-2002','H0018','F32.2','3.5',14,
  'Recurrent major depressive episode, severe, without psychotic features. Referred by the '
||'employer assistance programme.',
  'PENDED','STANDARD','Y', DATE '2026-08-14', NULL, NULL, NULL);

INSERT INTO BH_ASSESSMENT VALUES (700031,500004,'ASAM_DIM',1,0,DATE '2026-08-14');
INSERT INTO BH_ASSESSMENT VALUES (700032,500004,'ASAM_DIM',2,2,DATE '2026-08-14');
INSERT INTO BH_ASSESSMENT VALUES (700033,500004,'ASAM_DIM',3,3,DATE '2026-08-14');
INSERT INTO BH_ASSESSMENT VALUES (700034,500004,'ASAM_DIM',4,3,DATE '2026-08-14');
INSERT INTO BH_ASSESSMENT VALUES (700035,500004,'ASAM_DIM',5,3,DATE '2026-08-14');
INSERT INTO BH_ASSESSMENT VALUES (700036,500004,'ASAM_DIM',6,2,DATE '2026-08-14');
INSERT INTO BH_ASSESSMENT VALUES (700037,500004,'CSSRS',NULL,3,DATE '2026-08-14');
INSERT INTO BH_CONSENT   VALUES (800004,500004,'BW-1000405','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-08-14', DATE '2027-08-14', NULL, 'N');


-- ---------------------------------------------------------------------
-- 500005 -- branch 1, terminated provider. Commits immediately; the
-- assessment is never reached.
--
-- EXPECTED: DENIED, no level, 0 units, reason 'PROV_TERMED',
--           rule_path 'B1:termed;'
--
-- NOTE WHAT IS ODD HERE. This is the ONLY path on which the engine
-- returns DENIED, and it is an administrative denial rather than a
-- clinical one -- which is why the engine is allowed to issue it
-- without a physician. Every clinical adverse determination pends
-- instead (branch 9).
--
-- A decision table that simply "adds a DENIED output" without keeping
-- that distinction lets the engine issue clinical denials on its own.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500005,'BW-1000403','BWP-2006','H2036','F41.1','2.5',20,
  'Generalised anxiety disorder with panic features. Requesting partial hospitalisation.',
  'DENIED','STANDARD','N', DATE '2026-08-12', DATE '2026-08-12', 'BHAUTH_APP','PROV_TERMED');

INSERT INTO BH_ASSESSMENT VALUES (700041,500005,'ASAM_DIM',1,0,DATE '2026-08-12');
INSERT INTO BH_ASSESSMENT VALUES (700042,500005,'ASAM_DIM',3,3,DATE '2026-08-12');
INSERT INTO BH_CONSENT   VALUES (800005,500005,'BW-1000403','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-08-12', DATE '2027-08-12', NULL, 'N');


-- ---------------------------------------------------------------------
-- 500006 -- branch 9. Residential requested, criteria not met.
--
-- All dimensions 0, no C-SSRS -> score 0 at branch 7 and branch 8.
-- Requested level is 3.5, so branch 9 fires.
--
-- EXPECTED: PENDED, 1.0, 0 units, reason 'CRITERIA_NOT_MET'.
--
-- *** THE ENGINE DOES NOT DENY THIS, AND THAT IS DELIBERATE. ***
-- A nurse may approve; only a physician may issue an adverse
-- determination. PENDED is that separation of duties encoded as a
-- status. The donor platform's decision table cannot express it,
-- because the donor has no roles at all.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500006,'BW-1000406','BWP-2004','H0018','F41.1','3.5',14,
  'Anxiety with reported sleep disturbance. No prior treatment episodes. Member requesting '
||'residential placement.',
  'PENDED','STANDARD','N', DATE '2026-08-21', NULL, NULL, 'CRITERIA_NOT_MET');

INSERT INTO BH_ASSESSMENT VALUES (700051,500006,'ASAM_DIM',1,0,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700052,500006,'ASAM_DIM',2,0,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700053,500006,'ASAM_DIM',3,1,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700054,500006,'ASAM_DIM',4,4,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700055,500006,'ASAM_DIM',5,1,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700056,500006,'ASAM_DIM',6,1,DATE '2026-08-21');
INSERT INTO BH_CONSENT   VALUES (800006,500006,'BW-1000406','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-08-21', DATE '2027-08-21', NULL, 'N');


-- ---------------------------------------------------------------------
-- 500007 -- branch 6, the counter-intuitive one.
--
-- C-SSRS 4   -> +6  (score 6)
-- dim 3 = 3  -> +3  (score 9)
-- dim 4 = 0  -> -3  (score 6)   <-- READINESS TO CHANGE
--
-- A LOW readiness score REDUCES the case for residential, because
-- placement without engagement historically produces an
-- against-medical-advice discharge inside 72 hours.
--
-- Without branch 6 this case scores 9 and lands at 3.5. With it, 6, and
-- it lands at 2.5.
--
-- EXPECTED: APPROVED, 2.5, 20 units, 14-day interval.
--
-- Any modernized table that treats every dimension as a severity
-- indicator -- higher means more care -- gets this backwards.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500007,'BW-1000408','BWP-2004','H0035','F31.32','2.5',20,
  'Bipolar disorder, current episode depressed, moderate. Member ambivalent about treatment '
||'and has declined two prior referrals.',
  'APPROVED','STANDARD','N', DATE '2026-08-17', DATE '2026-08-17','rknowles', NULL);

INSERT INTO BH_ASSESSMENT VALUES (700061,500007,'ASAM_DIM',1,0,DATE '2026-08-17');
INSERT INTO BH_ASSESSMENT VALUES (700062,500007,'ASAM_DIM',2,1,DATE '2026-08-17');
INSERT INTO BH_ASSESSMENT VALUES (700063,500007,'ASAM_DIM',3,3,DATE '2026-08-17');
INSERT INTO BH_ASSESSMENT VALUES (700064,500007,'ASAM_DIM',4,0,DATE '2026-08-17');
INSERT INTO BH_ASSESSMENT VALUES (700065,500007,'ASAM_DIM',5,2,DATE '2026-08-17');
INSERT INTO BH_ASSESSMENT VALUES (700066,500007,'ASAM_DIM',6,2,DATE '2026-08-17');
INSERT INTO BH_ASSESSMENT VALUES (700067,500007,'CSSRS',NULL,4,DATE '2026-08-17');
INSERT INTO BH_CONSENT   VALUES (800007,500007,'BW-1000408','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-08-17', DATE '2027-08-17', NULL, 'N');

INSERT INTO BH_LOC_REVIEW VALUES (900011,500007,1,'2.5',20,14,DATE '2026-08-31','APPROVED',
  'rknowles','RN', DATE '2026-08-17');


-- ---------------------------------------------------------------------
-- 500008 -- the benefit cap, applied AFTER the ladder decides.
--
-- BW-1000407 has ZERO residential days remaining. Whatever the ladder
-- granted, LocRulesService adjustment A caps the units at 0 and
-- rewrites the outcome to PENDED / BENEFIT_EXHAUSTED.
--
-- The LEVEL is not rewritten. A member can end up granted ASAM 3.5 for
-- zero days, which is clinically incoherent and is what the system
-- does.
--
-- EXPECTED (full system, not the ladder alone):
--   PENDED, 3.5, 0 units, reason 'BENEFIT_EXHAUSTED'
--
-- This case only reproduces if BOTH rule layers are ported. Extract
-- the PL/SQL alone and it comes back APPROVED.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500008,'BW-1000407','BWP-2002','H0018','F10.20','3.5',14,
  'Alcohol use disorder, severe, with prior withdrawal seizure. Fourth treatment episode '
||'this benefit year.',
  'PENDED','STANDARD','N', DATE '2026-08-20', NULL, NULL, 'BENEFIT_EXHAUSTED');

INSERT INTO BH_ASSESSMENT VALUES (700071,500008,'ASAM_DIM',1,2,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700072,500008,'ASAM_DIM',2,2,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700073,500008,'ASAM_DIM',3,3,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700074,500008,'ASAM_DIM',4,3,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700075,500008,'ASAM_DIM',5,4,DATE '2026-08-20');
INSERT INTO BH_ASSESSMENT VALUES (700076,500008,'ASAM_DIM',6,4,DATE '2026-08-20');
INSERT INTO BH_CONSENT   VALUES (800008,500008,'BW-1000407','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-08-20', DATE '2027-08-20', NULL, 'N');


-- ---------------------------------------------------------------------
-- 500009 -- *** NO CONSENT ROW. ***
--
-- A Part 2 program (BWP-2005) with a clinical narrative and NOTHING in
-- BH_CONSENT. Under the current design this state should be
-- unreachable: AuthCaseService writes the authorization and the consent
-- in one transaction, so one cannot exist without the other.
--
-- It exists because this row predates BHA-0311 -- the consent table was
-- applied to production in January 2012 and to UAT in April, and two
-- months of data was created in between. See schema_changes.txt.
--
-- KEEP IT. test_consent_atomicity.py needs a row that proves the state
-- is representable in the DATA even though it is unreachable through
-- the CODE. A decomposed system where the two writes are separate makes
-- it reachable again, and this row is what the assertion looks like.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500009,'BW-1000409','BWP-2005','H0015','F11.20','2.1',30,
  'Opioid use disorder in early remission. Requesting intensive outpatient with contingency '
||'management. Transport is a barrier three days a week.',
  'APPROVED','STANDARD','N', DATE '2026-07-30', DATE '2026-07-31','rknowles', NULL);

-- Ladder arithmetic for this case, which runs through branch 1's OON arm:
--   BWP-2005 is OUT of network -> branch 1, -2  (score -2)
--   C-SSRS 3                   -> branch 2, +3  (score  1)
--   dim 5 = 3                  -> branch 5, +2  (score  3)
--   dim 4 = 3                  -> branch 6 does NOT fire
-- Branch 7 and the 2.5 arm of branch 8 both fail; score >= 2 gives 2.1.
-- EXPECTED: APPROVED, 2.1, 30 units, 30-day interval.
INSERT INTO BH_ASSESSMENT VALUES (700081,500009,'ASAM_DIM',1,1,DATE '2026-07-30');
INSERT INTO BH_ASSESSMENT VALUES (700082,500009,'ASAM_DIM',5,3,DATE '2026-07-30');
INSERT INTO BH_ASSESSMENT VALUES (700083,500009,'ASAM_DIM',6,3,DATE '2026-07-30');
INSERT INTO BH_ASSESSMENT VALUES (700084,500009,'ASAM_DIM',4,3,DATE '2026-07-30');
INSERT INTO BH_ASSESSMENT VALUES (700085,500009,'CSSRS',NULL,3,DATE '2026-07-30');
INSERT INTO BH_LOC_REVIEW VALUES (900021,500009,1,'2.1',30,30,DATE '2026-08-29','APPROVED',
  'rknowles','RN', DATE '2026-07-31');
-- (no BH_CONSENT row -- deliberate)


-- ---------------------------------------------------------------------
-- 500010 -- the EDI case. Arrived through X12278ImportJob.
--
-- NO NARRATIVE: the 278 has no segment for it and no trading partner
-- sends an attachment.
-- ALL DIMENSIONS ZERO: the 278 carries no assessment, so the importer
-- passes zeros and the ladder walks to its default branch.
-- SUBMITTED BY A SERVICE ACCOUNT with role mask 0 and credential
-- UNKNOWN -- which is what BH_LOC_REVIEW.REVIEWER_CREDENTIAL records,
-- defeating the 2015 audit finding that column was added for.
--
-- EXPECTED: PENDED, 1.0, 0 units, reason 'CRITERIA_NOT_MET'.
--
-- Follow the arithmetic. Every dimension is zero, so dimension 4 is
-- zero too -- and branch 6 reads a low readiness score as a reason
-- AGAINST residential placement, subtracting 3. The score reaches
-- branch 9 at -3, the requested level is 3.5, and the case pends.
--
-- SO EVERY EDI-SUBMITTED RESIDENTIAL REQUEST PENDS, and it pends
-- carrying a reason code that says the clinical criteria were not met
-- when in fact no clinical information was ever transmitted. Reviewers
-- know this and re-key the assessment from a phone call, which is why
-- review sequence 2 has a completely different level from sequence 1.
--
-- An agent that reads branch 6 as "severity" rather than "readiness"
-- will not reproduce this, and the difference is invisible until an
-- EDI batch runs.
--
-- The consent below was FABRICATED by the importer. Nobody verified it.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500010,'BW-1000401','BWP-2001','H0018','F10.20','3.5',14,
  NULL,
  'APPROVED','STANDARD','N', DATE '2026-08-11', DATE '2026-08-12','rknowles', NULL);

INSERT INTO BH_ASSESSMENT VALUES (700091,500010,'ASAM_DIM',1,0,DATE '2026-08-11');
INSERT INTO BH_ASSESSMENT VALUES (700092,500010,'ASAM_DIM',2,0,DATE '2026-08-11');
INSERT INTO BH_ASSESSMENT VALUES (700093,500010,'ASAM_DIM',3,0,DATE '2026-08-11');
INSERT INTO BH_ASSESSMENT VALUES (700094,500010,'ASAM_DIM',4,0,DATE '2026-08-11');
INSERT INTO BH_ASSESSMENT VALUES (700095,500010,'ASAM_DIM',5,0,DATE '2026-08-11');
INSERT INTO BH_ASSESSMENT VALUES (700096,500010,'ASAM_DIM',6,0,DATE '2026-08-11');
INSERT INTO BH_CONSENT   VALUES (800010,500010,'BW-1000401','Health plan (EDI trading partner)',
  'HEALTH_PLAN','Utilization review -- consent obtained at point of service',
  'AUTH_DECISION_ONLY', DATE '2026-08-11', DATE '2027-08-11', NULL, 'N');

-- Sequence 1: what the engine decided from zeros. Sequence 2: what the
-- reviewer decided after telephoning the facility. Two rungs, three
-- levels of care apart.
INSERT INTO BH_LOC_REVIEW VALUES (900031,500010,1,'1.0', 0,90,DATE '2026-11-09','PENDED',
  'bhauth_ws','UNKNOWN', DATE '2026-08-11');
INSERT INTO BH_LOC_REVIEW VALUES (900032,500010,2,'3.5',14, 7,DATE '2026-08-19','APPROVED',
  'rknowles','RN',       DATE '2026-08-12');


-- ---------------------------------------------------------------------
-- 500011 -- a revoked consent, and an authorization decided while it
-- was still active.
--
-- The revocation is prospective and the system holds no register of
-- what was disclosed under the consent before it was revoked. The
-- question "what went out under this?" has no answer here.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500011,'BW-1000410','BWP-2003','H0019','F11.20','3.7',10,
  'Opioid withdrawal management. Member declined medication for opioid use disorder at intake '
||'and has since reconsidered.',
  'APPROVED','EXPEDITED','N', DATE '2026-07-15', DATE '2026-07-15','tokafor', NULL);

INSERT INTO BH_ASSESSMENT VALUES (700101,500011,'ASAM_DIM',1,4,DATE '2026-07-15');
INSERT INTO BH_ASSESSMENT VALUES (700102,500011,'ASAM_DIM',4,1,DATE '2026-07-15');
INSERT INTO BH_CONSENT   VALUES (800011,500011,'BW-1000410','Northgate Recovery Center',
  'PROVIDER','Coordination of continuing care','FULL_RECORD',
  DATE '2026-07-15', DATE '2027-07-15', DATE '2026-08-04', 'Y');
INSERT INTO BH_LOC_REVIEW VALUES (900041,500011,1,'4.0',5,3,DATE '2026-07-18','APPROVED',
  'tokafor','MD_ADDICTION', DATE '2026-07-15');
INSERT INTO BH_LOC_REVIEW VALUES (900042,500011,2,'3.7',5,5,DATE '2026-07-23','STEPPED_DOWN',
  'tokafor','MD_ADDICTION', DATE '2026-07-18');
INSERT INTO BH_LOC_REVIEW VALUES (900043,500011,3,'3.7',5,5,NULL,             'DISCHARGED',
  'rknowles','RN',          DATE '2026-07-23');


-- ---------------------------------------------------------------------
-- 500012 -- the frequency pend, and the unactioned parity note.
--
-- BW-1000403 has three adverse determinations in the rolling year, so
-- LocRulesService adjustment B pends this case for a medical director
-- regardless of what the ladder decided.
--
-- Compliance flagged that adjustment in 2016: the medical side applies
-- no equivalent frequency-based pend to med/surg requests, which makes
-- it a non-quantitative treatment limitation applied to behavioral
-- health with no comparative analysis on file. The note was never
-- actioned.
--
-- A modernization that ports this rule forward carries the exposure
-- forward with it. A modernization that drops it silently changes
-- outcomes. Neither is a decision an agent should make alone --
-- ESCALATE IT.
-- ---------------------------------------------------------------------
INSERT INTO BH_AUTH VALUES (500012,'BW-1000403','BWP-2002','H0018','F33.2','3.5',14,
  'Recurrent depression with two hospitalisations this year. Outpatient engagement has been '
||'inconsistent.',
  'PENDED','STANDARD','N', DATE '2026-08-21', NULL, NULL, 'FREQUENCY_REVIEW');

INSERT INTO BH_ASSESSMENT VALUES (700111,500012,'ASAM_DIM',3,3,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700112,500012,'ASAM_DIM',5,3,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700113,500012,'ASAM_DIM',6,3,DATE '2026-08-21');
INSERT INTO BH_ASSESSMENT VALUES (700114,500012,'CSSRS',NULL,4,DATE '2026-08-21');
INSERT INTO BH_CONSENT   VALUES (800012,500012,'BW-1000403','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-08-21', DATE '2027-08-21', NULL, 'N');

-- The three prior denials that trip the frequency pend.
INSERT INTO BH_AUTH VALUES (500013,'BW-1000403','BWP-2004','H2036','F41.1','2.5',20,
  'Prior request, denied.','DENIED','STANDARD','N',
  DATE '2026-02-10', DATE '2026-02-12','pvasquez','CRITERIA_NOT_MET');
INSERT INTO BH_AUTH VALUES (500014,'BW-1000403','BWP-2004','H0018','F41.1','3.1',14,
  'Prior request, denied.','DENIED','STANDARD','N',
  DATE '2026-04-03', DATE '2026-04-05','pvasquez','CRITERIA_NOT_MET');
INSERT INTO BH_AUTH VALUES (500015,'BW-1000403','BWP-2004','H2036','F41.1','2.5',20,
  'Prior request, denied.','DENIED','STANDARD','N',
  DATE '2026-06-19', DATE '2026-06-20','pvasquez','CRITERIA_NOT_MET');

INSERT INTO BH_CONSENT VALUES (800013,500013,'BW-1000403','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-02-10', DATE '2027-02-10', NULL, 'N');
INSERT INTO BH_CONSENT VALUES (800014,500014,'BW-1000403','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-04-03', DATE '2027-04-03', NULL, 'N');
INSERT INTO BH_CONSENT VALUES (800015,500015,'BW-1000403','Bridgeway Behavioral Health',
  'HEALTH_PLAN','Utilization review','AUTH_DECISION_ONLY',
  DATE '2026-06-19', DATE '2027-06-19', NULL, 'N');


-- =====================================================================
-- OUTBOUND QUEUE
--
-- Note row 100003: STATE = 'LOCKED', enqueued weeks ago, LOCKED_BY a
-- worker that is no longer running. There is no lease, no timeout and
-- no reaper -- it stays LOCKED until a human sets it back to NEW.
--
-- Note also what the payloads contain. The clinical narrative, in a
-- VARCHAR2(4000), truncated to fit, on its way to an email to the
-- requesting provider's office. Two of these are from Part 2 programs
-- whose consent is scoped AUTH_DECISION_ONLY.
-- =====================================================================
INSERT INTO BH_AUTH_QUEUE VALUES (100001,500003,'AUTH_DECIDED',
  '{"authId":500003,"memberId":"BW-1000404","outcome":"APPROVED","grantedLoc":"4.0",'
||'"narrative":"Opioid use disorder with concurrent benzodiazepine use. Autonomic instability '
||'noted on assessment. Requires medically managed withdrawal."}',
  'DONE','poll-01', DATE '2026-08-20', DATE '2026-08-20');

INSERT INTO BH_AUTH_QUEUE VALUES (100002,500007,'AUTH_DECIDED',
  '{"authId":500007,"memberId":"BW-1000408","outcome":"APPROVED","grantedLoc":"2.5",'
||'"narrative":"Bipolar disorder, current episode depressed, moderate. Member ambivalent about '
||'treatment and has declined two prior referrals."}',
  'DONE','poll-01', DATE '2026-08-17', DATE '2026-08-17');

-- Stuck since 4 August. Nobody cleared it.
INSERT INTO BH_AUTH_QUEUE VALUES (100003,500011,'AUTH_DECIDED',
  '{"authId":500011,"memberId":"BW-1000410","outcome":"APPROVED","grantedLoc":"3.7",'
||'"narrative":"Opioid withdrawal management. Member declined medication for opioid use '
||'disorder at intake and has since reconsidered."}',
  'LOCKED','poll-01', DATE '2026-08-04', NULL);

INSERT INTO BH_AUTH_QUEUE VALUES (100004,500001,'AUTH_SUBMITTED',
  '{"authId":500001,"memberId":"BW-1000401","outcome":null,"grantedLoc":null,'
||'"narrative":"Member presents following a third emergency department contact this quarter."}',
  'NEW', NULL, DATE '2026-08-18', NULL);


-- =====================================================================
-- AUDIT LOG
--
-- Written in production by TRG_BH_AUTH_AUDIT. Seeded here to show two
-- things the trigger produces:
--
--   1. NARRATIVE COPIES. Audit 4 holds the full old and new narrative
--      for one status change. An authorization touched twelve times
--      over a residential stay leaves twelve of these. The audit table
--      has no consent scope and no expiry.
--
--   2. UNATTRIBUTED ROWS. Audits 2 and 5 are attributed to BHAUTH_APP,
--      the schema owner, because the Oracle session context was not set
--      on the connection that performed the update. That is the only
--      actor-attribution mechanism in the system.
-- =====================================================================
INSERT INTO BH_AUDIT_LOG VALUES (1,500003,'UPDATE','pvasquez',  4,'SUBMITTED','APPROVED',
  NULL, NULL, DATE '2026-08-20');
INSERT INTO BH_AUDIT_LOG VALUES (2,500005,'UPDATE','BHAUTH_APP',0,'SUBMITTED','DENIED',
  NULL, NULL, DATE '2026-08-12');
INSERT INTO BH_AUDIT_LOG VALUES (3,500007,'UPDATE','rknowles',  2,'IN_REVIEW','APPROVED',
  NULL, NULL, DATE '2026-08-17');
INSERT INTO BH_AUDIT_LOG VALUES (4,500001,'UPDATE','rknowles',  2,'SUBMITTED','IN_REVIEW',
  'Member presents following a third emergency department contact this quarter.',
  'Member presents following a third emergency department contact this quarter. Reports '
||'escalating passive ideation with a specific plan disclosed at triage. Outpatient contact '
||'has been irregular. Requesting medically monitored inpatient care for stabilisation.',
  DATE '2026-08-18');
INSERT INTO BH_AUDIT_LOG VALUES (5,500010,'UPDATE','BHAUTH_APP',0,'SUBMITTED','APPROVED',
  NULL, NULL, DATE '2026-08-11');


-- =====================================================================
-- Move the sequences past the explicit ids above.
-- =====================================================================
DROP   SEQUENCE SEQ_BH_AUTH_ID;
CREATE SEQUENCE SEQ_BH_AUTH_ID    START WITH 500100 INCREMENT BY 1 NOCACHE;
DROP   SEQUENCE SEQ_BH_REVIEW_ID;
CREATE SEQUENCE SEQ_BH_REVIEW_ID  START WITH 900100 INCREMENT BY 1 NOCACHE;
DROP   SEQUENCE SEQ_BH_ASSESS_ID;
CREATE SEQUENCE SEQ_BH_ASSESS_ID  START WITH 700200 INCREMENT BY 1 NOCACHE;
DROP   SEQUENCE SEQ_BH_CONSENT_ID;
CREATE SEQUENCE SEQ_BH_CONSENT_ID START WITH 800100 INCREMENT BY 1 NOCACHE;
DROP   SEQUENCE SEQ_BH_QUEUE_ID;
CREATE SEQUENCE SEQ_BH_QUEUE_ID   START WITH 100100 INCREMENT BY 1 NOCACHE;
DROP   SEQUENCE SEQ_BH_AUDIT_ID;
CREATE SEQUENCE SEQ_BH_AUDIT_ID   START WITH 100    INCREMENT BY 1 NOCACHE;

COMMIT;
