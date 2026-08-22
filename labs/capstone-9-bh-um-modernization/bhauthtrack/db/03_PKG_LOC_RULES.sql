-- =====================================================================
-- PKG_LOC_RULES -- the level-of-care rules engine.
--
-- Original author left Bridgeway in 2016. There is no design document.
-- The clinical policy team maintains the thresholds by emailing a
-- spreadsheet to whoever is on call, who edits this package by hand.
--
-- READ THIS BEFORE CHANGING ANYTHING:
--
-- EVAL_LOC does NOT evaluate a set of independent rules. It walks a
-- ladder from most intensive to least, accumulating into v_score, and
-- RETURNS AT THE FIRST BRANCH THAT COMMITS. Several branches fall
-- through deliberately -- they adjust v_score and keep going. That
-- means the order of the branches is load-bearing, and two branches
-- can both be "true" for the same input while only the first one that
-- commits produces the answer.
--
-- Anyone converting this to a declarative decision table has to decide
-- what the equivalent hit policy is, and prove it, because a naive
-- one-row-per-branch translation changes answers wherever branches
-- overlap. The 3.5 / 3.7 boundary is where that bites.
-- =====================================================================

CREATE OR REPLACE PACKAGE PKG_LOC_RULES AS

    -- Outcome codes returned by EVAL_LOC.
    C_APPROVE   CONSTANT VARCHAR2(20) := 'APPROVED';
    C_PEND      CONSTANT VARCHAR2(20) := 'PENDED';
    C_DENY      CONSTANT VARCHAR2(20) := 'DENIED';

    TYPE t_decision IS RECORD (
        outcome         VARCHAR2(20),
        granted_loc     VARCHAR2(8),
        granted_units   NUMBER(5),
        interval_days   NUMBER(3),
        reason_code     VARCHAR2(16),
        rule_path       VARCHAR2(200)   -- breadcrumb of branches taken
    );

    FUNCTION EVAL_LOC (p_auth_id IN NUMBER) RETURN t_decision;

    FUNCTION REVIEW_INTERVAL (p_loc IN VARCHAR2) RETURN NUMBER;

END PKG_LOC_RULES;
/

CREATE OR REPLACE PACKAGE BODY PKG_LOC_RULES AS

    -- -----------------------------------------------------------------
    -- Continued-stay cadence by level of care. These are regulatory
    -- review deadlines, not reminders. A residential authorization that
    -- is not re-reviewed within seven days is out of compliance.
    -- -----------------------------------------------------------------
    FUNCTION REVIEW_INTERVAL (p_loc IN VARCHAR2) RETURN NUMBER IS
    BEGIN
        CASE p_loc
            WHEN '4.0' THEN RETURN 3;    -- medically managed intensive inpatient
            WHEN '3.7' THEN RETURN 5;    -- medically monitored intensive inpatient
            WHEN '3.5' THEN RETURN 7;    -- clinically managed high-intensity residential
            WHEN '3.1' THEN RETURN 14;   -- clinically managed low-intensity residential
            WHEN '2.5' THEN RETURN 14;   -- partial hospitalization
            WHEN '2.1' THEN RETURN 30;   -- intensive outpatient
            WHEN '1.0' THEN RETURN 90;   -- outpatient
            ELSE RETURN 30;
        END CASE;
    END REVIEW_INTERVAL;


    FUNCTION EVAL_LOC (p_auth_id IN NUMBER) RETURN t_decision IS
        r            t_decision;
        v_score      NUMBER(4) := 0;      -- MUTATED ACROSS BRANCHES. This is the trap.
        v_req_loc    VARCHAR2(8);
        v_req_units  NUMBER(5);
        v_dx         VARCHAR2(10);
        v_svc        VARCHAR2(10);
        v_urgency    VARCHAR2(12);
        v_net        VARCHAR2(16);
        v_override   CHAR(1);
        v_d1 NUMBER(3) := 0;  -- ASAM dim 1: acute intoxication / withdrawal
        v_d2 NUMBER(3) := 0;  -- dim 2: biomedical conditions
        v_d3 NUMBER(3) := 0;  -- dim 3: emotional / behavioral / cognitive
        v_d4 NUMBER(3) := 0;  -- dim 4: readiness to change
        v_d5 NUMBER(3) := 0;  -- dim 5: relapse / continued use potential
        v_d6 NUMBER(3) := 0;  -- dim 6: recovery environment
        v_cssrs NUMBER(3) := 0;
        v_prior_denials NUMBER(3) := 0;
    BEGIN
        r.rule_path := '';

        SELECT a.REQUESTED_LOC, a.REQUESTED_UNITS, a.DIAGNOSIS_CODE,
               a.SERVICE_CODE, a.URGENCY, p.NETWORK_STATUS, a.LEGACY_OVERRIDE
          INTO v_req_loc, v_req_units, v_dx, v_svc, v_urgency, v_net, v_override
          FROM BH_AUTH a
          JOIN BH_PROVIDER p ON p.BRIDGEWAY_PROV_ID = a.BRIDGEWAY_PROV_ID
         WHERE a.AUTH_ID = p_auth_id;

        SELECT NVL(MAX(CASE WHEN DIMENSION = 1 THEN SCORE END), 0),
               NVL(MAX(CASE WHEN DIMENSION = 2 THEN SCORE END), 0),
               NVL(MAX(CASE WHEN DIMENSION = 3 THEN SCORE END), 0),
               NVL(MAX(CASE WHEN DIMENSION = 4 THEN SCORE END), 0),
               NVL(MAX(CASE WHEN DIMENSION = 5 THEN SCORE END), 0),
               NVL(MAX(CASE WHEN DIMENSION = 6 THEN SCORE END), 0)
          INTO v_d1, v_d2, v_d3, v_d4, v_d5, v_d6
          FROM BH_ASSESSMENT
         WHERE AUTH_ID = p_auth_id AND INSTRUMENT = 'ASAM_DIM';

        SELECT NVL(MAX(SCORE), 0) INTO v_cssrs
          FROM BH_ASSESSMENT
         WHERE AUTH_ID = p_auth_id AND INSTRUMENT = 'CSSRS';

        -- =============================================================
        -- BRANCH 0 -- the undocumented escape hatch.
        --
        -- Added under BHA-2291 (2013). The ticket says only "per DM
        -- request". Nobody currently at Bridgeway can say which cases
        -- this is meant to cover or who authorised it. It is still
        -- set on live rows.
        --
        -- DO NOT GUESS WHAT THIS MEANS.
        -- =============================================================
        IF v_override = 'Y' THEN
            r.outcome       := C_PEND;
            r.granted_loc   := v_req_loc;
            r.granted_units := 0;
            r.interval_days := REVIEW_INTERVAL(v_req_loc);
            r.reason_code   := 'LEGACY_OVR';
            r.rule_path     := 'B0:override';
            RETURN r;
        END IF;

        -- =============================================================
        -- BRANCH 1 -- out-of-network. FALLS THROUGH: it penalises the
        -- score and keeps evaluating rather than deciding here.
        -- =============================================================
        IF v_net = 'TERMED' THEN
            r.outcome       := C_DENY;
            r.granted_loc   := NULL;
            r.granted_units := 0;
            r.interval_days := 0;
            r.reason_code   := 'PROV_TERMED';
            r.rule_path     := r.rule_path || 'B1:termed;';
            RETURN r;
        ELSIF v_net = 'OUT' THEN
            v_score := v_score - 2;
            r.rule_path := r.rule_path || 'B1:oon(-2);';
            -- no RETURN: falls through
        END IF;

        -- =============================================================
        -- BRANCH 2 -- imminent risk. FALLS THROUGH on the moderate arm.
        -- =============================================================
        IF v_cssrs >= 4 THEN
            v_score := v_score + 6;
            r.rule_path := r.rule_path || 'B2:cssrs>=4(+6);';
        ELSIF v_cssrs = 3 THEN
            v_score := v_score + 3;
            r.rule_path := r.rule_path || 'B2:cssrs=3(+3);';
        END IF;

        -- =============================================================
        -- BRANCH 3 -- withdrawal severity (ASAM dimension 1).
        -- A high dimension-1 score alone justifies medically managed
        -- care regardless of everything below. COMMITS.
        -- =============================================================
        IF v_d1 >= 4 THEN
            r.outcome       := C_APPROVE;
            r.granted_loc   := '4.0';
            r.granted_units := LEAST(v_req_units, 5);
            r.interval_days := REVIEW_INTERVAL('4.0');
            r.reason_code   := NULL;
            r.rule_path     := r.rule_path || 'B3:d1>=4=>4.0;';
            RETURN r;
        ELSIF v_d1 = 3 THEN
            v_score := v_score + 4;
            r.rule_path := r.rule_path || 'B3:d1=3(+4);';
            -- no RETURN: falls through
        END IF;

        -- =============================================================
        -- BRANCH 4 -- biomedical + emotional load.
        -- =============================================================
        IF v_d2 >= 3 OR v_d3 >= 3 THEN
            v_score := v_score + 3;
            r.rule_path := r.rule_path || 'B4:d2|d3>=3(+3);';
        END IF;

        -- =============================================================
        -- BRANCH 5 -- relapse potential and recovery environment.
        -- These are what separate 3.5 from 3.7 in practice: a member
        -- can be clinically stable but living somewhere that makes
        -- outpatient care futile.
        -- =============================================================
        IF v_d5 >= 4 AND v_d6 >= 4 THEN
            v_score := v_score + 5;
            r.rule_path := r.rule_path || 'B5:d5&d6>=4(+5);';
        ELSIF v_d5 >= 3 OR v_d6 >= 3 THEN
            v_score := v_score + 2;
            r.rule_path := r.rule_path || 'B5:d5|d6>=3(+2);';
        END IF;

        -- =============================================================
        -- BRANCH 6 -- readiness to change. A LOW score here REDUCES
        -- the case for residential, because residential placement for
        -- a member with no engagement historically produces an
        -- against-medical-advice discharge inside 72 hours.
        -- =============================================================
        IF v_d4 <= 1 THEN
            v_score := v_score - 3;
            r.rule_path := r.rule_path || 'B6:d4<=1(-3);';
        END IF;

        -- =============================================================
        -- BRANCH 7 -- THE OVERLAP. Read carefully.
        --
        -- Both of the next two conditions can be true at once. A case
        -- with v_score = 10 and v_d1 = 3 -- reached by C-SSRS 4 (+6)
        -- and dimension 1 = 3 (+4) -- satisfies the 3.7 test AND would
        -- satisfy the 3.5 test below it. Because this is a
        -- first-commit ladder, it lands on 3.7 -- the MORE intensive
        -- level -- and the 3.5 branch never runs.
        --
        -- See auth 500001 in 02_seed.sql. It is that case exactly.
        --
        -- Flatten these into an unordered decision table and the
        -- answer depends entirely on the hit policy you pick. A
        -- unique-hit table errors on these rows. A collect-hit table
        -- returns both. Only a first-hit table preserves the behaviour,
        -- and only if the row order survives the translation.
        -- =============================================================
        IF v_score >= 10 AND v_d1 >= 3 THEN
            r.outcome       := C_APPROVE;
            r.granted_loc   := '3.7';
            r.granted_units := LEAST(v_req_units, 10);
            r.interval_days := REVIEW_INTERVAL('3.7');
            r.reason_code   := NULL;
            r.rule_path     := r.rule_path || 'B7a:score>=10&d1>=3=>3.7;';
            RETURN r;
        END IF;

        IF v_score >= 8 THEN
            r.outcome       := C_APPROVE;
            r.granted_loc   := '3.5';
            r.granted_units := LEAST(v_req_units, 14);
            r.interval_days := REVIEW_INTERVAL('3.5');
            r.reason_code   := NULL;
            r.rule_path     := r.rule_path || 'B7b:score>=8=>3.5;';
            RETURN r;
        END IF;

        -- =============================================================
        -- BRANCH 8 -- step-down levels.
        -- =============================================================
        IF v_score >= 5 THEN
            r.outcome       := C_APPROVE;
            r.granted_loc   := '2.5';
            r.granted_units := LEAST(v_req_units, 20);
            r.interval_days := REVIEW_INTERVAL('2.5');
            r.reason_code   := NULL;
            r.rule_path     := r.rule_path || 'B8:score>=5=>2.5;';
            RETURN r;
        ELSIF v_score >= 2 THEN
            r.outcome       := C_APPROVE;
            r.granted_loc   := '2.1';
            r.granted_units := LEAST(v_req_units, 30);
            r.interval_days := REVIEW_INTERVAL('2.1');
            r.reason_code   := NULL;
            r.rule_path     := r.rule_path || 'B8:score>=2=>2.1;';
            RETURN r;
        END IF;

        -- =============================================================
        -- BRANCH 9 -- the member asked for more than the criteria
        -- support. This is an ADVERSE DETERMINATION and it may not be
        -- issued automatically: only a physician may deny. The engine
        -- pends it for a medical director. It never returns DENIED
        -- here, and that is deliberate.
        -- =============================================================
        IF v_req_loc IN ('3.1','3.5','3.7','4.0') THEN
            r.outcome       := C_PEND;
            r.granted_loc   := '1.0';
            r.granted_units := 0;
            r.interval_days := REVIEW_INTERVAL('1.0');
            r.reason_code   := 'CRITERIA_NOT_MET';
            r.rule_path     := r.rule_path || 'B9:req>=3.1,score<2=>PEND;';
            RETURN r;
        END IF;

        -- =============================================================
        -- BRANCH 10 -- routine outpatient. Approve.
        -- =============================================================
        r.outcome       := C_APPROVE;
        r.granted_loc   := '1.0';
        r.granted_units := LEAST(v_req_units, 12);
        r.interval_days := REVIEW_INTERVAL('1.0');
        r.reason_code   := NULL;
        r.rule_path     := r.rule_path || 'B10:default=>1.0;';
        RETURN r;

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            r.outcome     := C_PEND;
            r.reason_code := 'DATA_MISSING';
            r.rule_path   := 'EX:no_data';
            RETURN r;
    END EVAL_LOC;

END PKG_LOC_RULES;
/
