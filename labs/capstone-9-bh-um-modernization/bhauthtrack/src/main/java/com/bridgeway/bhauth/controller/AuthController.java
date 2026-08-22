package com.bridgeway.bhauth.controller;

import com.bridgeway.bhauth.dao.AssessmentDao;
import com.bridgeway.bhauth.dao.AuditDao;
import com.bridgeway.bhauth.dao.AuthDao;
import com.bridgeway.bhauth.dao.ConsentDao;
import com.bridgeway.bhauth.dao.LocReviewDao;
import com.bridgeway.bhauth.dao.MemberDao;
import com.bridgeway.bhauth.domain.Auth;
import com.bridgeway.bhauth.domain.Consent;
import com.bridgeway.bhauth.domain.LocDecision;
import com.bridgeway.bhauth.security.UserContext;
import com.bridgeway.bhauth.service.AuthCaseService;
import com.bridgeway.bhauth.service.LocRulesService;
import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

/**
 * Authorization screens. Server-rendered: every method returns a JSP view name and populates the
 * model the JSP reads.
 *
 * <p>This is the file to read when working out what the REST surface of a modernized system
 * needs to be — but read it knowing that <b>the view names are not the whole story</b>. Each
 * {@code return "decision"} hands off to a JSP that computes things this controller never sees
 * and enforces rules this controller never checks. The controller and its view are one unit; a
 * port that lifts only the controller loses half of it.</p>
 *
 * <p>Note the model attributes each method sets. Those are the actual response contract.</p>
 */
@Controller
@RequestMapping("/auth")
public class AuthController {

    private static final Logger LOG = Logger.getLogger(AuthController.class);

    @Autowired private AuthCaseService authCaseService;
    @Autowired private LocRulesService locRulesService;
    @Autowired private AuthDao authDao;
    @Autowired private MemberDao memberDao;
    @Autowired private ConsentDao consentDao;
    @Autowired private LocReviewDao locReviewDao;
    @Autowired private AssessmentDao assessmentDao;
    @Autowired private AuditDao auditDao;
    @Autowired private UserContext userContext;

    /** GET /auth/new — the intake form. */
    @RequestMapping(value = "/new", method = RequestMethod.GET)
    public String newAuth(Model model) {
        if (!userContext.hasRole(UserContext.ROLE_INTAKE)
                && !userContext.hasRole(UserContext.ROLE_NURSE)) {
            return "redirect:/worklist";
        }
        model.addAttribute("auth", new Auth());
        return "authSubmit";
    }

    /**
     * POST /auth — submit a request.
     *
     * <p>The six ASAM dimension scores arrive as six separate request parameters named
     * {@code dim1}..{@code dim6} and are packed into the {@code int[][]} the service wants. The
     * consent fields arrive on the same form. One HTTP request carries the authorization, the
     * assessment and the consent, and they are written in one transaction — the form and the
     * transaction boundary are the same shape, which is not a coincidence.</p>
     *
     * <p><b>There is no validation here.</b> No required-field check, no code-set check, no range
     * check on the dimension scores. The database's CHECK constraints are the validation layer,
     * and where there is no constraint — dimension scores, for instance — there is none at
     * all.</p>
     */
    @RequestMapping(method = RequestMethod.POST)
    public String submit(@ModelAttribute("auth") Auth auth,
                         @RequestParam(value = "dim1", defaultValue = "0") int dim1,
                         @RequestParam(value = "dim2", defaultValue = "0") int dim2,
                         @RequestParam(value = "dim3", defaultValue = "0") int dim3,
                         @RequestParam(value = "dim4", defaultValue = "0") int dim4,
                         @RequestParam(value = "dim5", defaultValue = "0") int dim5,
                         @RequestParam(value = "dim6", defaultValue = "0") int dim6,
                         @RequestParam(value = "consentRecipient", required = false) String recipient,
                         @RequestParam(value = "consentScope", required = false) String scope,
                         @RequestParam(value = "consentPurpose", required = false) String purpose,
                         Model model) {

        List<int[]> dims = new ArrayList<int[]>();
        dims.add(new int[] { 1, dim1 });
        dims.add(new int[] { 2, dim2 });
        dims.add(new int[] { 3, dim3 });
        dims.add(new int[] { 4, dim4 });
        dims.add(new int[] { 5, dim5 });
        dims.add(new int[] { 6, dim6 });

        Consent consent = buildConsent(recipient, scope, purpose);

        try {
            Auth saved = authCaseService.submitAndDecide(auth, dims, consent);
            return "redirect:/auth/" + saved.getAuthId();
        } catch (RuntimeException e) {
            // The whole transaction rolled back -- authorization, assessments and consent alike.
            // The clinician is told to resubmit. There is no draft, so they retype everything,
            // including the narrative. This is the single most complained-about behaviour in the
            // application, and it is a direct consequence of the atomicity that makes it correct.
            LOG.error("submit failed for member=" + auth.getMemberId(), e);
            model.addAttribute("error",
                "The request could not be saved and nothing was recorded. Please resubmit.");
            return "authSubmit";
        }
    }

    /** GET /auth/{id} — the case detail screen. Tabs: request, clinical, decision, audit. */
    @RequestMapping(value = "/{authId}", method = RequestMethod.GET)
    public String detail(@PathVariable long authId, Model model) {
        Auth auth = authDao.findById(authId);
        model.addAttribute("auth", auth);
        model.addAttribute("member", memberDao.findById(auth.getMemberId()));
        model.addAttribute("provider", memberDao.findProvider(auth.getBridgewayProvId()));
        model.addAttribute("consent", consentDao.findByAuth(authId));
        model.addAttribute("reviews", locReviewDao.findByAuth(authId));
        model.addAttribute("assessments", assessmentDao.findByAuth(authId));
        // Loaded for every viewer, including those whose role hides the audit tab. The guard in
        // the JSP suppresses rendering; it does not suppress this query.
        model.addAttribute("auditEvents", auditDao.findByAuth(authId));
        return "authDetail";
    }

    /**
     * GET /auth/{id}/decide — the determination screen.
     *
     * <p>Note that this <b>re-runs the rules engine</b> to populate {@code decision}, because the
     * decision from submit time was never persisted. {@code LocDecision.rulePath} — the only
     * rationale this system produces — exists for the lifetime of a page render and is then
     * discarded. Reload the page a week later and you get today's answer computed from today's
     * benefit accumulators and today's bed availability, presented as if it were the original
     * determination.</p>
     */
    @RequestMapping(value = "/{authId}/decide", method = RequestMethod.GET)
    public String decideForm(@PathVariable long authId, Model model) {
        Auth auth = authDao.findById(authId);
        LocDecision decision = locRulesService.evaluate(authId);

        model.addAttribute("auth", auth);
        model.addAttribute("provider", memberDao.findProvider(auth.getBridgewayProvId()));
        model.addAttribute("consent", consentDao.findByAuth(authId));
        model.addAttribute("decision", decision);
        model.addAttribute("lastReview", locReviewDao.findLatest(authId));
        return "decision";
    }

    /**
     * POST /auth/{id}/decide — record a determination.
     *
     * <p>{@code action} comes from whichever submit button the reviewer pressed. The buttons the
     * reviewer <em>sees</em> are chosen by JSTL role guards in {@code decision.jsp}; the check
     * below is the server-side half, added in 2014 after an incident showed the view guard alone
     * was not enough.</p>
     */
    @RequestMapping(value = "/{authId}/decide", method = RequestMethod.POST)
    public String decide(@PathVariable long authId,
                         @RequestParam("action") String action,
                         @RequestParam(value = "reasonCode", required = false) String reasonCode,
                         Model model) {
        Auth auth = authDao.findById(authId);

        if ("DENY".equals(action)) {
            if (!userContext.mayDeny(auth.getDiagnosisCode())) {
                LOG.warn("deny refused user=" + userContext.getUserId()
                        + " mask=" + userContext.getRoleMask() + " authId=" + authId);
                model.addAttribute("error",
                    "An adverse determination on this diagnosis requires a same-specialty "
                  + "physician reviewer.");
                return decideForm(authId, model);
            }
            authCaseService.issueDenial(authId,
                    reasonCode == null ? "CRITERIA_NOT_MET" : reasonCode);

        } else if ("APPROVE".equals(action)) {
            authDao.updateStatus(authId, "APPROVED", null, userContext.getUserId());

        } else if ("PEND".equals(action)) {
            authDao.updateStatus(authId, "PENDED", "ADDITIONAL_CLINICAL",
                                 userContext.getUserId());

        } else if ("PEER_ROUTE".equals(action)) {
            // "Routing to peer review" sets a status and sends an email. There is no queue, no
            // assignment and no tracking; the case sits in PENDED until someone notices it.
            authDao.updateStatus(authId, "PENDED", "PEER_REVIEW", userContext.getUserId());

        } else {
            throw new IllegalArgumentException("Unknown action " + action);
        }

        return "redirect:/auth/" + authId;
    }

    /**
     * Build the Part 2 consent from the intake form.
     *
     * <p>Expiry is one year from signature, hard-coded here and nowhere else. A consent's
     * duration is a term of the consent itself, not a system default, so this is a policy
     * decision living in a controller.</p>
     */
    private Consent buildConsent(String recipient, String scope, String purpose) {
        Consent c = new Consent();
        c.setRecipientName(recipient == null ? "Bridgeway Behavioral Health" : recipient);
        c.setRecipientType(recipient == null ? "HEALTH_PLAN" : "OTHER");
        c.setPurpose(purpose == null ? "Utilization review and benefit determination" : purpose);
        c.setScope(scope == null ? "AUTH_DECISION_ONLY" : scope);
        c.setSignedTs(new Date());

        Calendar cal = Calendar.getInstance();
        cal.setTime(c.getSignedTs());
        cal.add(Calendar.YEAR, 1);
        c.setExpiresTs(cal.getTime());

        c.setRedisclosureNoticeSent("N");
        return c;
    }
}
