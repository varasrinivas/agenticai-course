package com.bridgeway.bhauth.security;

import com.bridgeway.bhauth.dao.UserRoleDao;
import org.apache.log4j.Logger;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.context.support.WebApplicationContextUtils;

import javax.naming.directory.Attributes;
import javax.naming.directory.DirContext;
import javax.naming.directory.InitialDirContext;
import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.IOException;
import java.util.Hashtable;

/**
 * Authentication and role loading. Mapped to {@code /*} in {@code web.xml}.
 *
 * <p>The whole security perimeter of BHAuthTrack, in one filter:</p>
 *
 * <ol>
 *   <li>Trust the container's {@code REMOTE_USER} — the app sits behind an IIS/SiteMinder
 *       reverse proxy that performs the actual sign-on. This application never sees a
 *       password and cannot verify the header it is trusting.</li>
 *   <li>Look the user up in LDAP to get their clinical credential.</li>
 *   <li>Look their role mask up in {@code BH_USER_ROLE}.</li>
 *   <li>Push both into the session-scoped {@link UserContext} <em>and</em>, separately, into
 *       raw session attributes, because the JSPs read {@code sessionScope.roleMask} directly
 *       rather than going through the bean.</li>
 * </ol>
 *
 * <h3>The duplication in step 4 is the finding</h3>
 *
 * <p>{@code UserContext.roleMask} and {@code session.getAttribute("roleMask")} are two copies of
 * the same value, set together here and never reconciled afterwards. The services read the
 * first; every JSP reads the second. Nothing keeps them in step — if a user's roles change
 * mid-session neither is refreshed, and a port that carries across only one of the two silently
 * changes who can see what.</p>
 *
 * <h3>Also worth noticing</h3>
 *
 * <p>The Oracle session context set at the bottom is what {@code TRG_BH_AUTH_AUDIT} reads to
 * record an actor. It is set <b>per HTTP request, on a pooled connection</b>. If the request
 * later uses a different connection from the pool — which happens whenever a service opens a
 * second transaction — the trigger records {@code USER}, the schema owner, instead of the human.
 * A non-trivial fraction of {@code BH_AUDIT_LOG} rows are attributed to {@code BHAUTH_APP}.</p>
 */
public class AuthFilter implements Filter {

    private static final Logger LOG = Logger.getLogger(AuthFilter.class);

    private static final String LDAP_URL  = "ldap://ldap.bridgeway.internal:389";
    private static final String LDAP_BASE = "ou=people,dc=bridgeway,dc=internal";

    private UserRoleDao userRoleDao;

    @Override
    public void init(FilterConfig cfg) throws ServletException {
        WebApplicationContext ctx = WebApplicationContextUtils
                .getRequiredWebApplicationContext(cfg.getServletContext());
        this.userRoleDao = ctx.getBean(UserRoleDao.class);
    }

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest  request  = (HttpServletRequest) req;
        HttpServletResponse response = (HttpServletResponse) res;

        // The proxy is the only authentication. If the header is absent we are either being
        // reached directly -- which should be impossible -- or the proxy is misconfigured.
        String userId = request.getRemoteUser();
        if (userId == null) {
            userId = request.getHeader("SM_USER");   // SiteMinder fallback, added 2013
        }
        if (userId == null) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, "No authenticated user");
            return;
        }

        HttpSession session = request.getSession(true);
        WebApplicationContext ctx = WebApplicationContextUtils
                .getRequiredWebApplicationContext(request.getServletContext());
        UserContext userContext = ctx.getBean(UserContext.class);

        if (!userId.equals(session.getAttribute("userId"))) {
            int    mask = 0;
            String cred = "UNKNOWN";
            try {
                mask = userRoleDao.findRoleMask(userId);
                cred = lookupCredential(userId);
            } catch (Exception e) {
                // Deliberately non-fatal: a directory outage in 2012 locked every reviewer out
                // for four hours, so the decision was taken to let them in with no roles rather
                // than not at all. A mask of 0 can still read; it can do nothing else.
                LOG.error("role/credential lookup failed for " + userId
                        + " -- continuing with mask 0", e);
            }

            userContext.setUserId(userId);
            userContext.setRoleMask(mask);
            userContext.setCredential(cred);

            // The second copy. Every JSP reads THIS one, not the bean above.
            session.setAttribute("userId", userId);
            session.setAttribute("roleMask", mask);
            session.setAttribute("credential", cred);

            LOG.info("session established user=" + userId + " mask=" + mask + " cred=" + cred);
        }

        // Tell Oracle who is acting, for TRG_BH_AUTH_AUDIT. See the class comment: this is set
        // on whichever pooled connection happens to be current.
        try {
            userRoleDao.setSessionActor(userId);
        } catch (Exception e) {
            LOG.warn("could not set BHAUTH_CTX for " + userId, e);
        }

        chain.doFilter(req, res);
    }

    /**
     * Read the clinical credential from the directory {@code title} attribute.
     *
     * <p>Free text, maintained by HR. The values this system understands are {@code RN},
     * {@code LCSW}, {@code MD}, {@code MD_PSYCH} and {@code MD_ADDICTION}. Anything else lands
     * as {@code UNKNOWN} and is written into {@code BH_LOC_REVIEW.REVIEWER_CREDENTIAL}, which
     * is the column a 2015 audit asked for so we could prove the reviewer was licensed.</p>
     */
    private String lookupCredential(String userId) throws Exception {
        Hashtable<String, String> env = new Hashtable<String, String>();
        env.put(DirContext.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.ldap.LdapCtxFactory");
        env.put(DirContext.PROVIDER_URL, LDAP_URL);
        env.put(DirContext.SECURITY_AUTHENTICATION, "simple");

        DirContext dctx = null;
        try {
            dctx = new InitialDirContext(env);
            Attributes attrs = dctx.getAttributes("uid=" + userId + "," + LDAP_BASE,
                                                  new String[] { "title" });
            Object title = attrs.get("title") == null ? null : attrs.get("title").get();
            return title == null ? "UNKNOWN" : normalise(title.toString());
        } finally {
            if (dctx != null) {
                try { dctx.close(); } catch (Exception ignore) { }
            }
        }
    }

    private String normalise(String title) {
        String t = title.trim().toUpperCase();
        if (t.contains("ADDICTION"))                 return "MD_ADDICTION";
        if (t.contains("PSYCHIATR"))                 return "MD_PSYCH";
        if (t.startsWith("MD") || t.contains("PHYSICIAN")) return "MD";
        if (t.contains("LCSW") || t.contains("SOCIAL")) return "LCSW";
        if (t.contains("RN") || t.contains("NURSE"))    return "RN";
        return "UNKNOWN";
    }

    @Override
    public void destroy() { }
}
