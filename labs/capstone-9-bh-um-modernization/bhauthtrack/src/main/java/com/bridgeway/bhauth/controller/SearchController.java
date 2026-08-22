package com.bridgeway.bhauth.controller;

import com.bridgeway.bhauth.dao.AuthDao;
import com.bridgeway.bhauth.dao.MemberDao;
import com.bridgeway.bhauth.security.UserContext;
import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * Search.
 *
 * <p>Three search modes on one screen, and they are not equally safe.</p>
 *
 * <ul>
 *   <li><b>By member id</b> — either identifier. See {@link #search}: it tries Bridgeway's key
 *       first and the plan's key second, silently. A user who pastes a plan identifier gets
 *       results and never learns which key matched.</li>
 *   <li><b>By member name</b> — ordinary.</li>
 *   <li><b>By clinical text</b> — a full CLOB scan across every narrative in the system,
 *       available to any authenticated user, with no role check and no consent check.</li>
 * </ul>
 *
 * <p>The third one is the finding. {@code decision.jsp} carefully hides the narrative from
 * intake coordinators with {@code &lt;c:if test="${sessionScope.roleMask ge 2}"&gt;} — and this
 * screen lets the same user search the full text of every narrative in the database and shows
 * matching authorization numbers. The minimum-necessary control on one screen is undone by the
 * absence of one on another.</p>
 *
 * <p>Modernizing this onto a search index without adding the missing check reproduces the flaw
 * at higher throughput and with a copy of the protected content in a second datastore.</p>
 */
@Controller
@RequestMapping("/search")
public class SearchController {

    private static final Logger LOG = Logger.getLogger(SearchController.class);

    @Autowired private AuthDao authDao;
    @Autowired private MemberDao memberDao;
    @Autowired private UserContext userContext;

    @RequestMapping(method = RequestMethod.GET)
    public String search(@RequestParam(value = "mode", required = false) String mode,
                         @RequestParam(value = "q", required = false) String q,
                         Model model) {

        if (q == null || q.trim().isEmpty()) {
            return "search";
        }
        String query = q.trim();
        model.addAttribute("q", query);
        model.addAttribute("mode", mode);

        if ("member".equals(mode)) {
            // Try Bridgeway's key, then the plan's. Which one matched is not reported.
            if (memberDao.findById(query) != null) {
                model.addAttribute("auths", authDao.findByMember(query));
                model.addAttribute("matchedOn", "MEMBER_ID");
            } else {
                java.util.List<com.bridgeway.bhauth.domain.Member> byPlan =
                    memberDao.findByPlanMemberId(query);
                if (!byPlan.isEmpty()) {
                    // If the plan identifier is duplicated -- and it can be, there is no unique
                    // constraint -- only the first member's authorizations are shown.
                    model.addAttribute("auths",
                        authDao.findByMember(byPlan.get(0).getMemberId()));
                    model.addAttribute("matchedOn", "PLAN_MEMBER_ID");
                    model.addAttribute("duplicatePlanIds", byPlan.size() > 1);
                }
            }

        } else if ("name".equals(mode)) {
            model.addAttribute("members", memberDao.searchByName(query));

        } else if ("clinical".equals(mode)) {
            // No role check. The narrative search is open to anyone who can reach this URL.
            LOG.info("clinical text search q=" + query + " by=" + userContext.getUserId());
            model.addAttribute("auths", authDao.searchNarrative(query));
        }

        return "search";
    }
}
