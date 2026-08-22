package com.bridgeway.bhauth.service;

import com.bridgeway.bhauth.dao.AuthDao;
import com.bridgeway.bhauth.dao.LocRulesDao;
import com.bridgeway.bhauth.domain.Auth;
import com.bridgeway.bhauth.domain.LocDecision;
import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Level-of-care rules.
 *
 * <p><b>The rules are in two places.</b> The bulk of the ladder is {@code PKG_LOC_RULES.EVAL_LOC}
 * in Oracle. This class calls it and then applies a second layer of adjustments in Java. The split
 * is historical: the PL/SQL was written in 2011, and when the parity and network-adequacy rules
 * arrived in 2015 the team that owned them could not get a database release slot, so they added
 * them here instead.</p>
 *
 * <p>Consequences that matter for anyone converting this to a decision table:</p>
 * <ul>
 *   <li>Neither layer alone is the rule set. You have to read both and merge them.</li>
 *   <li>The Java layer runs <em>after</em> the PL/SQL has already committed to an outcome, so it
 *       can only downgrade or pend, never upgrade. That asymmetry is load-bearing.</li>
 *   <li>The PL/SQL ladder is stateful first-match. This layer is order-dependent too. Flattening
 *       both into one unordered table changes answers wherever rows overlap.</li>
 * </ul>
 */
@Service
public class LocRulesService {

    private static final Logger LOG = Logger.getLogger(LocRulesService.class);

    /** ASAM levels ordered least to most intensive, for step-down comparisons. */
    private static final String[] LADDER =
        { "1.0", "2.1", "2.5", "3.1", "3.5", "3.7", "4.0" };

    @Autowired private LocRulesDao locRulesDao;
    @Autowired private AuthDao authDao;

    public LocDecision evaluate(long authId) {
        // Layer 1: the Oracle ladder.
        LocDecision d = locRulesDao.callEvalLoc(authId);
        Auth auth = authDao.findById(authId);

        // -----------------------------------------------------------------
        // Layer 2, adjustment A -- benefit maximum.
        //
        // Applied AFTER the ladder has chosen a level, so it silently caps
        // units without changing the level. A member granted 3.5 for 14 days
        // whose remaining benefit is 6 days gets 3.5 for 6 days, which is
        // clinically incoherent but is what the system does.
        // -----------------------------------------------------------------
        int remaining = locRulesDao.remainingBenefitDays(auth.getMemberId(), auth.getRequestedLoc());
        if (d.getGrantedUnits() > remaining) {
            LOG.info("benefit cap authId=" + authId
                    + " granted=" + d.getGrantedUnits() + " remaining=" + remaining);
            d.setGrantedUnits(remaining);
            if (remaining == 0) {
                d.setOutcome("PENDED");
                d.setReasonCode("BENEFIT_EXHAUSTED");
            }
        }

        // -----------------------------------------------------------------
        // Layer 2, adjustment B -- prior adverse determinations.
        //
        // Three or more denials in the rolling year pends the case for a
        // medical director regardless of what the ladder said.
        //
        // PARITY NOTE (added by compliance, 2016, never actioned):
        // "The medical side does not apply an equivalent frequency-based
        //  pend to med/surg requests. If we keep this we need a
        //  comparative analysis on file. -- K.O."
        // -----------------------------------------------------------------
        int priorDenials = locRulesDao.countDenialsInRollingYear(auth.getMemberId());
        if (priorDenials >= 3 && "APPROVED".equals(d.getOutcome())) {
            LOG.info("frequency pend authId=" + authId + " priorDenials=" + priorDenials);
            d.setOutcome("PENDED");
            d.setReasonCode("FREQUENCY_REVIEW");
        }

        // -----------------------------------------------------------------
        // Layer 2, adjustment C -- network adequacy step-down.
        //
        // If no in-network facility at the granted level has capacity, step
        // down one rung rather than authorising out-of-network. This runs
        // last and can therefore undo the ladder's decision entirely.
        // -----------------------------------------------------------------
        if ("APPROVED".equals(d.getOutcome()) && isResidential(d.getGrantedLoc())) {
            if (!locRulesDao.hasInNetworkCapacity(d.getGrantedLoc())) {
                String steppedDown = stepDown(d.getGrantedLoc());
                LOG.info("network step-down authId=" + authId
                        + " " + d.getGrantedLoc() + " -> " + steppedDown);
                d.setGrantedLoc(steppedDown);
                d.setIntervalDays(reviewInterval(steppedDown));
                d.setRulePath(d.getRulePath() + "J:C:stepdown;");
            }
        }

        return d;
    }

    /** Mirrors {@code PKG_LOC_RULES.REVIEW_INTERVAL}. Kept in sync by hand. */
    public int reviewInterval(String loc) {
        if (loc == null) return 30;
        switch (loc) {
            case "4.0": return 3;
            case "3.7": return 5;
            case "3.5": return 7;
            case "3.1": return 14;
            case "2.5": return 14;
            case "2.1": return 30;
            case "1.0": return 90;
            default:    return 30;
        }
    }

    private boolean isResidential(String loc) {
        return "3.1".equals(loc) || "3.5".equals(loc) || "3.7".equals(loc) || "4.0".equals(loc);
    }

    private String stepDown(String loc) {
        for (int i = 1; i < LADDER.length; i++) {
            if (LADDER[i].equals(loc)) return LADDER[i - 1];
        }
        return loc;
    }
}
