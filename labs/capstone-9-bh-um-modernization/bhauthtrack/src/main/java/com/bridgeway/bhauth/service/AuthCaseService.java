package com.bridgeway.bhauth.service;

import com.bridgeway.bhauth.dao.AuthDao;
import com.bridgeway.bhauth.dao.AssessmentDao;
import com.bridgeway.bhauth.dao.ConsentDao;
import com.bridgeway.bhauth.dao.LocReviewDao;
import com.bridgeway.bhauth.dao.QueueDao;
import com.bridgeway.bhauth.domain.Auth;
import com.bridgeway.bhauth.domain.Consent;
import com.bridgeway.bhauth.domain.LocDecision;
import com.bridgeway.bhauth.domain.LocReview;
import com.bridgeway.bhauth.security.UserContext;
import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.List;

/**
 * BHAuthTrack core service.
 *
 * <p>This class is 1,800 lines in the real system. What follows is the part that matters for
 * modernization: the submit-and-decide path. Everything else in here is CRUD, search, and
 * report-feeding queries.</p>
 *
 * <p>HISTORY: this started in 2011 as three separate services. They were merged in 2013 because
 * the transaction boundaries kept producing orphaned consent rows when the JTA config drifted
 * between environments. Merging them into one {@code @Transactional} method made the problem go
 * away. That fix is the reason this class is the shape it is, and it is the single most important
 * thing to understand before splitting it apart again.</p>
 *
 * @author  D. Reyes (left Bridgeway 2016)
 * @since   4.0
 */
@Service
public class AuthCaseService {

    private static final Logger LOG = Logger.getLogger(AuthCaseService.class);

    @Autowired private AuthDao authDao;
    @Autowired private AssessmentDao assessmentDao;
    @Autowired private ConsentDao consentDao;
    @Autowired private LocReviewDao locReviewDao;
    @Autowired private QueueDao queueDao;
    @Autowired private LocRulesService locRulesService;
    @Autowired private AuthStatusService authStatusService;
    @Autowired private UserContext userContext;

    /**
     * Accept a prior-authorization request, evaluate it, and record the outcome.
     *
     * <p><b>ATOMICITY.</b> This method performs five writes that must all happen or none of them:
     * the authorization row, the assessment rows, the Part 2 consent record, the initial
     * level-of-care review, and the outbound queue row. They are in one transaction against one
     * Oracle instance. If the consent write fails, the authorization is rolled back and the
     * clinician is told to resubmit.</p>
     *
     * <p>That is not a nicety. An authorization for a Part 2 program that exists without its
     * consent record is a disclosure we cannot lawfully act on: we would be holding protected
     * treatment content with no record of who the member agreed we may share it with. Under this
     * design that state is unrepresentable. Any redesign has to say what makes it unrepresentable
     * instead, because "we'll write the consent row right after" is not an answer.</p>
     */
    @Transactional(propagation = Propagation.REQUIRED, rollbackFor = Exception.class)
    public Auth submitAndDecide(Auth auth, List<int[]> asamDimensions, Consent consent) {

        // --- Write 1: the authorization -------------------------------------------------
        long authId = authDao.nextAuthId();
        auth.setAuthId(authId);
        auth.setStatus("SUBMITTED");
        auth.setSubmittedTs(new Date());
        authDao.insert(auth);

        // NOTE: the clinical narrative is logged here so the appeals team can reconstruct what
        // the clinician originally submitted when a decision is challenged months later. It has
        // been this way since 4.0. Log4j writes to a rolling file on the app server, which is
        // backed up nightly to the same share the reporting team reads from.
        LOG.info("submitAndDecide authId=" + authId
                + " member=" + auth.getMemberId()
                + " svc=" + auth.getServiceCode()
                + " dx=" + auth.getDiagnosisCode()
                + " reqLoc=" + auth.getRequestedLoc()
                + " narrative=" + auth.getClinicalNarrative());

        // --- Write 2: the assessments ---------------------------------------------------
        for (int[] dim : asamDimensions) {
            assessmentDao.insertAsamDimension(authId, dim[0], dim[1]);
        }

        // --- Write 3: the Part 2 consent ------------------------------------------------
        // Only required when the requesting provider is a federally assisted SUD program, but we
        // capture it unconditionally because the provider flag has been wrong before.
        consent.setAuthId(authId);
        consent.setMemberId(auth.getMemberId());
        consentDao.insert(consent);

        // --- Decide ---------------------------------------------------------------------
        LocDecision decision = locRulesService.evaluate(authId);

        // --- Write 4: the initial level-of-care review ----------------------------------
        // REVIEW_SEQ 1 is the initial determination. Everything after it is continued stay.
        // NEXT_REVIEW_DUE is what drives the concurrent-review worklist; an approval without it
        // is an authorization nobody will ever look at again.
        LocReview initial = new LocReview();
        initial.setAuthId(authId);
        initial.setReviewSeq(1);
        initial.setReviewedLoc(decision.getGrantedLoc());
        initial.setApprovedUnits(decision.getGrantedUnits());
        initial.setReviewIntervalDays(decision.getIntervalDays());
        initial.setNextReviewDue(addDays(new Date(), decision.getIntervalDays()));
        initial.setOutcome(decision.getOutcome());
        initial.setReviewerUserId(userContext.getUserId());
        initial.setReviewerCredential(userContext.getCredential());
        initial.setReviewTs(new Date());
        locReviewDao.insert(initial);

        // --- Advance the status ---------------------------------------------------------
        authStatusService.advance(auth, decision);
        authDao.updateStatus(authId, auth.getStatus(), decision.getReasonCode(),
                             userContext.getUserId());

        // --- Write 5: the outbound queue row --------------------------------------------
        // There is no broker. poll_queue.sh picks this up from cron every five minutes and
        // hands it to the notification job. PAYLOAD is capped at 4000 chars because it is a
        // VARCHAR2, which is why the narrative is truncated rather than omitted.
        queueDao.enqueue(authId, "AUTH_DECIDED",
                "{\"authId\":" + authId
              + ",\"memberId\":\"" + auth.getMemberId() + "\""
              + ",\"outcome\":\"" + decision.getOutcome() + "\""
              + ",\"grantedLoc\":\"" + decision.getGrantedLoc() + "\""
              + ",\"narrative\":\"" + truncate(auth.getClinicalNarrative(), 2000) + "\"}");

        LOG.info("submitAndDecide complete authId=" + authId
                + " outcome=" + decision.getOutcome()
                + " grantedLoc=" + decision.getGrantedLoc()
                + " rulePath=" + decision.getRulePath());

        return auth;
    }

    /**
     * Record a continued-stay review.
     *
     * <p>This is the half of behavioral-health utilization management that medical prior auth does
     * not have. An authorization is not one decision; it is an initial decision plus a series of
     * reviews on a cadence set by level of care. The worklist is driven off NEXT_REVIEW_DUE.</p>
     */
    @Transactional(propagation = Propagation.REQUIRED, rollbackFor = Exception.class)
    public LocReview recordContinuedStay(long authId, String reviewedLoc, int approvedUnits,
                                         String outcome) {
        int nextSeq = locReviewDao.maxSeq(authId) + 1;
        int interval = locRulesService.reviewInterval(reviewedLoc);

        LocReview review = new LocReview();
        review.setAuthId(authId);
        review.setReviewSeq(nextSeq);
        review.setReviewedLoc(reviewedLoc);
        review.setApprovedUnits(approvedUnits);
        review.setReviewIntervalDays(interval);
        // A discharge closes the ladder. Anything else schedules the next review.
        review.setNextReviewDue("DISCHARGED".equals(outcome)
                ? null : addDays(new Date(), interval));
        review.setOutcome(outcome);
        review.setReviewerUserId(userContext.getUserId());
        review.setReviewerCredential(userContext.getCredential());
        review.setReviewTs(new Date());
        locReviewDao.insert(review);

        LOG.info("continuedStay authId=" + authId + " seq=" + nextSeq
                + " loc=" + reviewedLoc + " outcome=" + outcome
                + " nextDue=" + review.getNextReviewDue());
        return review;
    }

    /**
     * Issue an adverse determination.
     *
     * <p>Guarded here as well as in the view, because the view guard was added first and this one
     * was added in 2014 after an incident. A nurse may approve; only a physician may deny. For
     * substance-use and psychiatric level-of-care the reviewer is expected to be same-specialty.</p>
     */
    @Transactional(propagation = Propagation.REQUIRED, rollbackFor = Exception.class)
    public void issueDenial(long authId, String reasonCode) {
        if (!userContext.hasRole(UserContext.ROLE_MD)) {
            throw new IllegalStateException(
                "Adverse determination requires a physician reviewer; user "
                + userContext.getUserId() + " has mask " + userContext.getRoleMask());
        }
        Auth auth = authDao.findById(authId);
        if (isSubstanceUseDiagnosis(auth.getDiagnosisCode())
                && !userContext.hasRole(UserContext.ROLE_MD_ADDICTION)) {
            LOG.warn("SUD denial by non-addiction physician authId=" + authId
                    + " user=" + userContext.getUserId());
        }
        authDao.updateStatus(authId, "DENIED", reasonCode, userContext.getUserId());
    }

    private boolean isSubstanceUseDiagnosis(String icd10) {
        return icd10 != null && icd10.length() >= 3
                && icd10.charAt(0) == 'F'
                && icd10.compareTo("F10") >= 0 && icd10.compareTo("F20") < 0;
    }

    private static String truncate(String s, int max) {
        if (s == null) return "";
        return s.length() <= max ? s : s.substring(0, max);
    }

    private static Date addDays(Date from, int days) {
        if (days <= 0) return null;
        return new Date(from.getTime() + (long) days * 86400000L);
    }
}
