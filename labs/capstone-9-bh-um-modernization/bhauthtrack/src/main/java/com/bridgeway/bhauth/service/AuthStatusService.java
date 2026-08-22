package com.bridgeway.bhauth.service;

import com.bridgeway.bhauth.domain.Auth;
import com.bridgeway.bhauth.domain.LocDecision;
import com.bridgeway.bhauth.security.UserContext;
import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * The workflow. There isn't one.
 *
 * <p>What there is, is a STATUS column and this switch. Every transition in BHAuthTrack goes
 * through {@link #advance}. There is no process engine, no timer, no task list and no diagram.
 * The concurrent-review cadence lives in {@code BH_LOC_REVIEW.NEXT_REVIEW_DUE} and is surfaced by
 * a nightly query that builds the worklist; nothing enforces that a review actually happens.</p>
 *
 * <p>Reading this switch is how you recover the process model. Note especially that
 * {@code APPROVED} is <em>not</em> terminal here the way it would be in a one-shot prior-auth
 * system: an approved authorization re-enters review on its cadence, and can be stepped down or
 * discharged from there.</p>
 */
@Service
public class AuthStatusService {

    private static final Logger LOG = Logger.getLogger(AuthStatusService.class);

    @Autowired private UserContext userContext;

    /**
     * Advance an authorization based on the rules engine's outcome.
     *
     * <p>Legal transitions, recovered from this method:</p>
     * <pre>
     *   SUBMITTED  -> IN_REVIEW | PENDED | APPROVED
     *   IN_REVIEW  -> PENDED | APPROVED | DENIED
     *   PENDED     -> IN_REVIEW | APPROVED | DENIED
     *   APPROVED   -> IN_REVIEW   (continued stay -- NOT terminal)
     *              -> EXPIRED     (cadence missed, see nightly job)
     *   DENIED     -> (terminal here; appeals are handled outside this system entirely,
     *                  in a shared mailbox and a spreadsheet)
     *   EXPIRED    -> (terminal)
     * </pre>
     */
    public void advance(Auth auth, LocDecision decision) {
        final String from = auth.getStatus();
        final String outcome = decision.getOutcome();

        switch (from) {

            case "SUBMITTED":
                if ("APPROVED".equals(outcome)) {
                    // Auto-approval. Permitted only when the engine committed on a criteria
                    // branch -- never on the override branch.
                    if ("LEGACY_OVR".equals(decision.getReasonCode())) {
                        auth.setStatus("PENDED");
                    } else {
                        auth.setStatus("APPROVED");
                    }
                } else if ("PENDED".equals(outcome)) {
                    auth.setStatus("PENDED");
                } else if ("DENIED".equals(outcome)) {
                    // The engine is not allowed to deny on its own. If it somehow returns
                    // DENIED at intake, we pend it for a physician instead. A nurse may
                    // approve; only a physician may issue an adverse determination.
                    LOG.warn("engine returned DENIED at intake authId=" + auth.getAuthId()
                            + " -- coercing to PENDED for physician review");
                    auth.setStatus("PENDED");
                } else {
                    auth.setStatus("IN_REVIEW");
                }
                break;

            case "IN_REVIEW":
                if ("APPROVED".equals(outcome)) {
                    auth.setStatus("APPROVED");
                } else if ("DENIED".equals(outcome)) {
                    if (!userContext.hasRole(UserContext.ROLE_MD)) {
                        throw new IllegalStateException(
                            "Adverse determination requires a physician reviewer");
                    }
                    auth.setStatus("DENIED");
                } else {
                    auth.setStatus("PENDED");
                }
                break;

            case "PENDED":
                // ---------------------------------------------------------------------
                // BHA-2291 (2013). The ticket body reads, in full: "per DM request".
                //
                // Nobody currently at Bridgeway can say what this branch is for, which
                // determinations it was meant to cover, or who "DM" was. It is still set
                // on live rows -- roughly 400 of them as of the last extract.
                //
                // It has been left in place because removing it changes the outcome for
                // those rows and nobody is willing to sign off on what the new outcome
                // should be.
                //
                // DO NOT GUESS WHAT THIS MEANS. Escalate it.
                // ---------------------------------------------------------------------
                if ("Y".equals(auth.getLegacyOverride())) {
                    LOG.warn("LEGACY_OVERRIDE path taken authId=" + auth.getAuthId()
                            + " -- see BHA-2291, undocumented");
                    auth.setStatus("IN_REVIEW");
                    break;
                }
                if ("APPROVED".equals(outcome)) {
                    auth.setStatus("APPROVED");
                } else if ("DENIED".equals(outcome)) {
                    if (!userContext.hasRole(UserContext.ROLE_MD)) {
                        throw new IllegalStateException(
                            "Adverse determination requires a physician reviewer");
                    }
                    auth.setStatus("DENIED");
                } else {
                    auth.setStatus("IN_REVIEW");
                }
                break;

            case "APPROVED":
                // Continued stay. An approved authorization is not finished; it comes back
                // around on its cadence. This is the single biggest structural difference
                // from medical prior auth, and it is expressed here as a status that loops.
                auth.setStatus("IN_REVIEW");
                break;

            case "DENIED":
            case "EXPIRED":
                throw new IllegalStateException(
                    "Cannot advance terminal status " + from + " authId=" + auth.getAuthId());

            default:
                throw new IllegalStateException("Unknown status " + from);
        }

        LOG.info("advance authId=" + auth.getAuthId()
                + " " + from + " -> " + auth.getStatus()
                + " outcome=" + outcome
                + " actor=" + userContext.getUserId());
    }
}
