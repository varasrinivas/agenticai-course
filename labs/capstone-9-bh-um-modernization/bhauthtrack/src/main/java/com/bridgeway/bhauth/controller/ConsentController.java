package com.bridgeway.bhauth.controller;

import com.bridgeway.bhauth.dao.ConsentDao;
import com.bridgeway.bhauth.dao.MemberDao;
import com.bridgeway.bhauth.security.UserContext;
import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * 42 CFR Part 2 consent administration.
 *
 * <p><b>Educational model, not legal advice.</b> The behaviour encoded here is a simplified
 * teaching version of the regulation, sufficient to make the architectural point and not
 * sufficient to build a compliance programme on.</p>
 *
 * <p>Admin-only, and it is the one screen in the system where the role check is at the top of
 * every method rather than in the view. That is not virtue: it was written in 2012 by a
 * different developer, before the convention of guarding in JSTL took hold. Two conventions
 * coexist in this codebase and an inventory of "where authorization happens" has to find
 * both.</p>
 */
@Controller
@RequestMapping("/member/{memberId}/consent")
public class ConsentController {

    private static final Logger LOG = Logger.getLogger(ConsentController.class);

    @Autowired private ConsentDao consentDao;
    @Autowired private MemberDao memberDao;
    @Autowired private UserContext userContext;

    /** GET — every consent on file for this member. */
    @RequestMapping(method = RequestMethod.GET)
    public String list(@PathVariable String memberId, Model model) {
        if (!userContext.hasRole(UserContext.ROLE_ADMIN)) {
            return "redirect:/worklist";
        }
        model.addAttribute("member", memberDao.findById(memberId));
        model.addAttribute("consents", consentDao.findByMember(memberId));
        return "consentAdmin";
    }

    /**
     * POST /revoke — revoke a consent.
     *
     * <p>Sets a timestamp and returns. It does not recall what was already disclosed, does not
     * notify the recipient the consent named, and does not flag the authorizations that were
     * decided while it was active. Under the regulation a revocation is prospective, so that is
     * defensible — but nothing here even records which disclosures happened under it, because
     * this system has no accounting of disclosures at all.</p>
     *
     * <p>The audit table records changes to authorizations. It does not record who a record was
     * disclosed to, when, or under which consent. That register is what a Part 2 programme has to
     * be able to produce, and building it is one of the {@code must-build-new} items.</p>
     */
    @RequestMapping(value = "/revoke", method = RequestMethod.POST)
    public String revoke(@PathVariable String memberId,
                         @RequestParam("consentId") long consentId) {
        if (!userContext.hasRole(UserContext.ROLE_ADMIN)) {
            return "redirect:/worklist";
        }
        consentDao.revoke(consentId, userContext.getUserId());
        LOG.info("consent revoked consentId=" + consentId + " member=" + memberId
                + " by=" + userContext.getUserId());
        return "redirect:/member/" + memberId + "/consent";
    }

    /**
     * POST /notice — record that the redisclosure notice accompanied a disclosure.
     *
     * <p>A checkbox on a screen. Nothing verifies that a notice was actually sent, and nothing
     * blocks a disclosure whose box is unticked.</p>
     */
    @RequestMapping(value = "/notice", method = RequestMethod.POST)
    public String markNotice(@PathVariable String memberId,
                             @RequestParam("consentId") long consentId) {
        if (!userContext.hasRole(UserContext.ROLE_ADMIN)) {
            return "redirect:/worklist";
        }
        consentDao.markNoticeSent(consentId);
        return "redirect:/member/" + memberId + "/consent";
    }
}
