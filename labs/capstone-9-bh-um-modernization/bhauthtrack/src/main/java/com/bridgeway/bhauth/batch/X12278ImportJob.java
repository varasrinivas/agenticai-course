package com.bridgeway.bhauth.batch;

import com.bridgeway.bhauth.domain.Auth;
import com.bridgeway.bhauth.domain.Consent;
import com.bridgeway.bhauth.service.AuthCaseService;
import org.apache.log4j.Logger;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

/**
 * Nightly X12 278 import. Quartz, cron {@code 0 15 2 * * ?} — 02:15 every day.
 *
 * <p>X12 278 is the EDI transaction for a health-care services review request. Payers and large
 * provider groups send them in batches; Bridgeway receives a file per trading partner on an SFTP
 * drop and this job walks the drop directory.</p>
 *
 * <h3>Why this job matters to a modernization far more than its size suggests</h3>
 *
 * <p>The modern platform's intake is a REST endpoint: one request, one case, synchronous, with an
 * idempotency story available if anyone wants one. This job is the opposite on every axis, and
 * each difference is a decision somebody has to make deliberately rather than discover:</p>
 *
 * <ol>
 *   <li><b>No idempotency key.</b> There is nothing in the file or the database that identifies a
 *       transaction as already-processed. The guard is {@link #alreadyImported}, which matches on
 *       member + service code + requested level + submission date. Two genuinely distinct
 *       requests for the same member, same service, same day are indistinguishable from a
 *       duplicate, and the second is dropped. This has happened.</li>
 *   <li><b>Whole-file semantics.</b> A file either processes or is moved to {@code failed/} and
 *       reprocessed by hand the next morning — for the whole day, not the failed row.</li>
 *   <li><b>It bypasses the controller.</b> Requests enter through
 *       {@code AuthCaseService.submitAndDecide()} directly, so every check that lives in
 *       {@code AuthController} or in a JSP does not run. This is one of the four call paths
 *       mentioned in {@code decision.jsp}'s maintenance note.</li>
 *   <li><b>It fabricates the consent.</b> See {@link #impliedConsent}.</li>
 * </ol>
 *
 * <p>A real-time REST intake is the right target. Getting there means answering "what is the
 * idempotency key?" and "who consents when a machine submits?", and neither answer is in this
 * code — only the absence of one.</p>
 */
public class X12278ImportJob implements Job {

    private static final Logger LOG = Logger.getLogger(X12278ImportJob.class);

    private static final String DROP_DIR = "/opt/bhauth/sftp/inbound/278";

    @Autowired private AuthCaseService authCaseService;
    @Autowired private com.bridgeway.bhauth.dao.AuthDao authDao;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        File dir = new File(DROP_DIR);
        File[] files = dir.listFiles();
        if (files == null) {
            LOG.error("278 drop directory unreadable: " + DROP_DIR);
            return;
        }

        int imported = 0, skipped = 0, failed = 0;

        for (File f : files) {
            if (!f.getName().endsWith(".278")) continue;
            try {
                List<Auth> batch = parse(f);
                for (Auth auth : batch) {
                    if (alreadyImported(auth)) {
                        skipped++;
                        continue;
                    }
                    // Straight into the service. No controller, no validation, no role context:
                    // the Quartz thread has no HTTP session, so UserContext is unpopulated and
                    // the review row is written with a null reviewer.
                    authCaseService.submitAndDecide(auth, dimensionsFrom(auth), impliedConsent(auth));
                    imported++;
                }
                move(f, "processed");
            } catch (Exception e) {
                // The whole file fails, not the row. Tomorrow morning someone edits the file by
                // hand to remove the offending transaction and drops it back in.
                LOG.error("278 file failed, moving to failed/: " + f.getName(), e);
                move(f, "failed");
                failed++;
            }
        }

        LOG.info("278 import complete imported=" + imported
                + " skipped=" + skipped + " failedFiles=" + failed);
    }

    /**
     * Parse one 278 file.
     *
     * <p>Segment-and-element splitting by hand, because the EDI library the architecture team
     * chose in 2011 was never licensed. It reads the segments Bridgeway's trading partners
     * actually send and ignores the rest of the transaction set.</p>
     *
     * <p><b>Note what is missing.</b> There is no segment here carrying the clinical narrative.
     * A 278 can convey attachments and free text, but no trading partner sends them, so a
     * request arriving through this path has an empty narrative and reaches a reviewer with no
     * clinical justification to read. They telephone the facility.</p>
     */
    private List<Auth> parse(File f) throws Exception {
        List<Auth> out = new ArrayList<Auth>();
        BufferedReader r = null;
        try {
            r = new BufferedReader(new FileReader(f));
            String line;
            Auth current = null;
            while ((line = r.readLine()) != null) {
                String[] seg = line.split("\\*");
                if (seg.length == 0) continue;

                if ("HL".equals(seg[0]) && seg.length > 3 && "23".equals(seg[3])) {
                    // HL*n*n*23 -- a new dependent/subscriber level starts a new request
                    if (current != null) out.add(current);
                    current = new Auth();
                    current.setUrgency("STANDARD");
                    current.setLegacyOverride("N");
                    current.setClinicalNarrative(null);     // nothing in the file to put here
                } else if (current == null) {
                    continue;
                } else if ("NM1".equals(seg[0]) && seg.length > 9 && "IL".equals(seg[1])) {
                    current.setMemberId(seg[9]);           // subscriber id as sent
                } else if ("NM1".equals(seg[0]) && seg.length > 9 && "SJ".equals(seg[1])) {
                    current.setBridgewayProvId(seg[9]);    // servicing provider
                } else if ("UM".equals(seg[0]) && seg.length > 2) {
                    current.setRequestedLoc(mapServiceLevel(seg[2]));
                } else if ("HI".equals(seg[0]) && seg.length > 1) {
                    current.setDiagnosisCode(stripQualifier(seg[1]));
                } else if ("SV2".equals(seg[0]) && seg.length > 4) {
                    current.setServiceCode(seg[1]);
                    current.setRequestedUnits(parseIntSafe(seg[4]));
                }
            }
            if (current != null) out.add(current);
        } finally {
            if (r != null) {
                try { r.close(); } catch (Exception ignore) { }
            }
        }
        return out;
    }

    /**
     * The duplicate guard, and the reason this job is not safely re-runnable.
     *
     * <p>There is no transaction control number stored anywhere, so "have I seen this before?"
     * is answered by a heuristic: same member, same service code, same requested level, same
     * calendar day. A member who genuinely needs two authorizations for the same service on the
     * same day gets one.</p>
     */
    private boolean alreadyImported(Auth a) {
        List<Auth> existing = authDao.findByMember(a.getMemberId());
        Calendar today = Calendar.getInstance();
        for (Auth e : existing) {
            if (e.getSubmittedTs() == null) continue;
            Calendar c = Calendar.getInstance();
            c.setTime(e.getSubmittedTs());
            boolean sameDay = c.get(Calendar.YEAR) == today.get(Calendar.YEAR)
                           && c.get(Calendar.DAY_OF_YEAR) == today.get(Calendar.DAY_OF_YEAR);
            if (sameDay
                    && eq(e.getServiceCode(), a.getServiceCode())
                    && eq(e.getRequestedLoc(), a.getRequestedLoc())) {
                return true;
            }
        }
        return false;
    }

    /**
     * Fabricate a consent record for a machine-submitted request.
     *
     * <p>The transaction carries no consent, and {@code AuthCaseService.submitAndDecide()}
     * requires one — so this job invents one, scoped to the determination only, naming the plan
     * as recipient and asserting that consent was obtained on paper at the facility.</p>
     *
     * <p><b>Nobody verifies that.</b> It is an assumption written into a batch job in 2011 and
     * it applies to every request that arrives by EDI, which is most of them. If the archaeology
     * turns up one thing worth escalating to a compliance officer rather than to an architect,
     * it is this method.</p>
     */
    private Consent impliedConsent(Auth a) {
        Consent c = new Consent();
        c.setMemberId(a.getMemberId());
        c.setRecipientName("Health plan (EDI trading partner)");
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

    /**
     * ASAM dimensions for an EDI request: all zeros.
     *
     * <p>The 278 carries no assessment. Every dimension is zero, which walks the ladder to its
     * default branch — outpatient — regardless of what the facility actually requested. Reviewers
     * know this and re-key the assessment by hand from the phone call, which is why the
     * {@code REVIEW_SEQ 2} row often has a completely different level from {@code REVIEW_SEQ
     * 1}.</p>
     */
    private List<int[]> dimensionsFrom(Auth a) {
        List<int[]> dims = new ArrayList<int[]>();
        for (int d = 1; d <= 6; d++) dims.add(new int[] { d, 0 });
        return dims;
    }

    /** UM02 service-level code to ASAM level. Mapping maintained by hand, source unrecorded. */
    private String mapServiceLevel(String um02) {
        if ("IP".equals(um02)) return "3.7";
        if ("RS".equals(um02)) return "3.5";
        if ("PH".equals(um02)) return "2.5";
        if ("IO".equals(um02)) return "2.1";
        return "1.0";
    }

    private String stripQualifier(String hi) {
        int colon = hi.indexOf(':');
        return colon < 0 ? hi : hi.substring(colon + 1);
    }

    private int parseIntSafe(String s) {
        try { return Integer.parseInt(s.trim()); } catch (Exception e) { return 0; }
    }

    private boolean eq(String a, String b) {
        return a == null ? b == null : a.equals(b);
    }

    private void move(File f, String subdir) {
        File dest = new File(new File(DROP_DIR, subdir), f.getName());
        if (!f.renameTo(dest)) {
            LOG.error("could not move " + f.getName() + " to " + subdir
                    + " -- it will be reprocessed tomorrow");
        }
    }
}
