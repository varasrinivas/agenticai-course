package com.bridgeway.bhauth.controller;

import com.bridgeway.bhauth.dao.AuthDao;
import com.bridgeway.bhauth.dao.LocReviewDao;
import com.bridgeway.bhauth.dao.MemberDao;
import com.bridgeway.bhauth.domain.Auth;
import com.bridgeway.bhauth.security.UserContext;
import com.bridgeway.bhauth.service.AuthCaseService;
import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * Continued-stay review.
 *
 * <p>This controller has no equivalent in medical prior authorization, and that absence is the
 * shape of the whole problem. A medical case is decided once. A behavioral-health case is
 * decided, then reviewed again on a cadence — every three days at ASAM 4.0, every seven at 3.5 —
 * until the member is discharged or steps down. Each pass through {@link #record} appends a rung
 * to the ladder and schedules the next.</p>
 *
 * <p>The modernized platform's process model terminates after one decision. Whoever ports it has
 * to add a loop that does not exist in the donor, driven by a timer the donor does not have,
 * and this controller is the specification for it.</p>
 */
@Controller
@RequestMapping("/auth/{authId}/review")
public class ReviewController {

    private static final Logger LOG = Logger.getLogger(ReviewController.class);

    @Autowired private AuthCaseService authCaseService;
    @Autowired private LocReviewDao locReviewDao;
    @Autowired private AuthDao authDao;
    @Autowired private MemberDao memberDao;
    @Autowired private UserContext userContext;

    /** GET /auth/{id}/review — the continued-stay entry form. */
    @RequestMapping(method = RequestMethod.GET)
    public String form(@PathVariable long authId, Model model) {
        Auth auth = authDao.findById(authId);
        model.addAttribute("auth", auth);
        model.addAttribute("provider", memberDao.findProvider(auth.getBridgewayProvId()));
        model.addAttribute("reviews", locReviewDao.findByAuth(authId));
        model.addAttribute("lastReview", locReviewDao.findLatest(authId));
        model.addAttribute("nextSeq", locReviewDao.maxSeq(authId) + 1);
        return "locReview";
    }

    /**
     * POST /auth/{id}/review — record a continued-stay determination.
     *
     * <h3>The gap this method leaves open</h3>
     *
     * <p>{@code outcome} arrives from a dropdown whose options include {@code DENIED}. The
     * check below stops a nurse issuing one. What it does <em>not</em> do is any of what
     * {@code AuthCaseService.issueDenial()} does — no specialty check, and no update to
     * {@code BH_AUTH.STATUS}. A continued-stay denial recorded here appends a review row saying
     * DENIED while the authorization itself stays APPROVED.</p>
     *
     * <p>Nobody has fixed it because the worklist reads the review row, so the case does leave
     * the queue and it looks right from the screen a reviewer uses. It looks wrong from every
     * report, which read {@code BH_AUTH}.</p>
     */
    @RequestMapping(method = RequestMethod.POST)
    public String record(@PathVariable long authId,
                         @RequestParam("reviewedLoc") String reviewedLoc,
                         @RequestParam("approvedUnits") int approvedUnits,
                         @RequestParam("outcome") String outcome,
                         Model model) {

        if ("DENIED".equals(outcome) && !userContext.hasRole(UserContext.ROLE_MD)) {
            model.addAttribute("error",
                "A continued-stay denial is an adverse determination and requires a physician.");
            return form(authId, model);
        }

        authCaseService.recordContinuedStay(authId, reviewedLoc, approvedUnits, outcome);

        LOG.info("continued stay recorded authId=" + authId + " loc=" + reviewedLoc
                + " outcome=" + outcome + " by=" + userContext.getUserId());

        return "redirect:/auth/" + authId;
    }
}
