package com.bridgeway.bhauth.controller;

import com.bridgeway.bhauth.dao.WorklistDao;
import com.bridgeway.bhauth.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

/**
 * The worklist. The application's home screen and its work-distribution mechanism.
 *
 * <p>Six lines of controller wrapping one query. That ratio is the point: everything interesting
 * about how work reaches a reviewer is in {@code WorklistDao.forReviewer()} and in
 * {@code worklist.jsp}, and nothing is here.</p>
 *
 * <p>A port that inventories "the API" from controllers alone concludes the worklist is a
 * trivial list endpoint. It is the closest thing this system has to a task engine.</p>
 */
@Controller
public class WorklistController {

    @Autowired private WorklistDao worklistDao;
    @Autowired private UserContext userContext;

    /**
     * GET / and GET /worklist.
     *
     * <p>The role mask goes into the model as well as being used for the query, because
     * {@code worklist.jsp} filters a second time in JSTL. See {@code WorklistDao} for why the two
     * filters disagree.</p>
     */
    @RequestMapping(value = { "/", "/worklist" }, method = RequestMethod.GET)
    public String worklist(Model model) {
        model.addAttribute("items", worklistDao.forReviewer(userContext.getRoleMask()));
        model.addAttribute("roleMask", userContext.getRoleMask());
        model.addAttribute("credential", userContext.getCredential());
        return "worklist";
    }
}
