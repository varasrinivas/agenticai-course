package com.bridgeway.bhauth.ws;

import com.bridgeway.bhauth.domain.Auth;
import com.bridgeway.bhauth.domain.Consent;
import com.bridgeway.bhauth.service.AuthCaseService;
import org.apache.log4j.Logger;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.context.support.WebApplicationContextUtils;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

import org.w3c.dom.Document;
import org.w3c.dom.NodeList;

/**
 * The SOAP endpoint. Mapped to {@code /services/auth} in {@code web.xml}.
 *
 * <p>Written in 2012 for one trading partner who could not send X12, and never retired. It is
 * hand-rolled: a plain servlet, a DOM parse, and a string-concatenated response envelope,
 * because the SOAP stack the architecture team standardised on was never installed on this
 * server.</p>
 *
 * <h3>This is the fourth call path into the decision logic</h3>
 *
 * <p>The others are {@code AuthController}, {@code X12278ImportJob}, and a DBA at a SQL prompt.
 * Three of the four bypass every check that lives in a JSP, which is where three of this
 * system's business rules live. That is the concrete reason the {@code decision.jsp}
 * maintenance note tells you to treat a template as security-relevant.</p>
 *
 * <h3>Specifics worth carrying into an inventory</h3>
 *
 * <ul>
 *   <li><b>No authentication.</b> {@code AuthFilter} is mapped to {@code /*} and does run — but
 *       this partner's requests arrive from a fixed source IP allowed through the proxy without
 *       a user, so {@code REMOTE_USER} is a service account with role mask 0. Every review row
 *       this path creates is attributed to that account with credential {@code UNKNOWN}.</li>
 *   <li><b>No WSDL in source control.</b> The contract this partner codes against was emailed
 *       to them in 2012. What this servlet accepts is the contract.</li>
 *   <li><b>The narrative arrives here.</b> Unlike the X12 path, this envelope has a
 *       {@code &lt;clinicalNarrative&gt;} element, and the partner populates it. Protected
 *       content enters the system over a transport that terminates TLS at the proxy.</li>
 * </ul>
 */
public class LegacyAuthEndpoint extends HttpServlet {

    private static final long serialVersionUID = 1L;
    private static final Logger LOG = Logger.getLogger(LegacyAuthEndpoint.class);

    private AuthCaseService authCaseService;

    @Override
    public void init() throws ServletException {
        WebApplicationContext ctx = WebApplicationContextUtils
                .getRequiredWebApplicationContext(getServletContext());
        this.authCaseService = ctx.getBean(AuthCaseService.class);
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {

        resp.setContentType("text/xml; charset=UTF-8");
        PrintWriter out = resp.getWriter();

        try {
            DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
            // No secure-processing feature and no external-entity restriction. This has been
            // flagged in two penetration tests, in 2014 and 2017, and deferred both times on
            // the grounds that the endpoint is IP-restricted.
            DocumentBuilder b = f.newDocumentBuilder();
            Document doc = b.parse(req.getInputStream());

            Auth auth = new Auth();
            auth.setMemberId(text(doc, "memberId"));
            auth.setBridgewayProvId(text(doc, "providerId"));
            auth.setServiceCode(text(doc, "serviceCode"));
            auth.setDiagnosisCode(text(doc, "diagnosisCode"));
            auth.setRequestedLoc(text(doc, "requestedLoc"));
            auth.setRequestedUnits(intText(doc, "requestedUnits"));
            auth.setClinicalNarrative(text(doc, "clinicalNarrative"));
            auth.setUrgency("EXPEDITED".equals(text(doc, "urgency")) ? "EXPEDITED" : "STANDARD");
            auth.setLegacyOverride("N");

            List<int[]> dims = new ArrayList<int[]>();
            for (int d = 1; d <= 6; d++) {
                dims.add(new int[] { d, intText(doc, "asamDim" + d) });
            }

            Auth saved = authCaseService.submitAndDecide(auth, dims, impliedConsent(auth));

            out.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
            out.println("<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">");
            out.println("  <soap:Body>");
            out.println("    <submitAuthResponse>");
            out.println("      <authId>" + saved.getAuthId() + "</authId>");
            out.println("      <status>" + saved.getStatus() + "</status>");
            out.println("    </submitAuthResponse>");
            out.println("  </soap:Body>");
            out.println("</soap:Envelope>");

        } catch (Exception e) {
            // The narrative is in the request body and the request body is in the stack trace
            // whenever the DOM parse fails partway. Log4j writes it to the same rolling file as
            // everything else.
            LOG.error("SOAP submit failed", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            out.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
            out.println("<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">");
            out.println("  <soap:Body><soap:Fault>");
            out.println("    <faultcode>Server</faultcode>");
            out.println("    <faultstring>" + e.getMessage() + "</faultstring>");
            out.println("  </soap:Fault></soap:Body>");
            out.println("</soap:Envelope>");
        }
    }

    /**
     * As in the batch importer: a consent is fabricated because the caller does not send one and
     * {@code submitAndDecide} requires one.
     *
     * <p>Two independent code paths invent a Part 2 consent record on the caller's behalf. That
     * is not a bug in either of them individually — it is a design that has no answer to "who
     * consents when a machine submits?", implemented twice.</p>
     */
    private Consent impliedConsent(Auth a) {
        Consent c = new Consent();
        c.setMemberId(a.getMemberId());
        c.setRecipientName("Health plan (SOAP trading partner)");
        c.setRecipientType("HEALTH_PLAN");
        c.setPurpose("Utilization review -- consent obtained at point of service");
        c.setScope("AUTH_DECISION_ONLY");
        c.setSignedTs(new Date());
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.YEAR, 1);
        c.setExpiresTs(cal.getTime());
        c.setRedisclosureNoticeSent("N");
        return c;
    }

    private String text(Document doc, String tag) {
        NodeList n = doc.getElementsByTagName(tag);
        if (n.getLength() == 0 || n.item(0).getFirstChild() == null) return null;
        return n.item(0).getFirstChild().getNodeValue();
    }

    private int intText(Document doc, String tag) {
        String s = text(doc, tag);
        if (s == null) return 0;
        try { return Integer.parseInt(s.trim()); } catch (NumberFormatException e) { return 0; }
    }
}
