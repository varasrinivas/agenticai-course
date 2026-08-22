<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c"   uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ page import="com.bridgeway.bhauth.domain.LocReview" %>
<%--
  locReview.jsp -- continued-stay review entry.

  THIS SCREEN HAS NO EQUIVALENT IN MEDICAL PRIOR AUTHORIZATION, and it is the one to read
  before writing the BPMN. Every element on it corresponds to something the modernized process
  model needs and does not currently have:

    - a task that recurs on a timer rather than running once
    - a decision that can step a member DOWN a level rather than only approve or deny
    - a terminal outcome (DISCHARGED) that closes the loop
    - an interval that is recomputed from the NEW level, not the old one

  The step-down options below are generated from a ladder that is hard-coded in a scriptlet at
  the bottom of this file. That ladder also exists in LocRulesService.LADDER and in
  PKG_LOC_RULES. Three copies. They currently agree.
--%>
<html>
<head>
  <title>Continued stay &mdash; Auth ${auth.authId}</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>Continued-stay review</h1>

<c:if test="${provider.part2Program}">
  <div class="part2-banner">
    <strong>42 CFR Part 2 &mdash; protected record.</strong>
    Redisclosure prohibited except as permitted by a consent naming the recipient.
  </div>
</c:if>

<table class="authhdr">
  <tr><th>Authorization</th><td>${auth.authId}</td></tr>
  <tr><th>Member</th><td>${auth.memberId}</td></tr>
  <tr><th>Diagnosis</th><td>${auth.diagnosisCode}</td></tr>
  <tr><th>Current level of care</th><td>${lastReview.reviewedLoc}</td></tr>
  <tr><th>Units approved to date</th><td>${lastReview.approvedUnits}</td></tr>
  <tr><th>This review</th><td>sequence ${nextSeq}</td></tr>
  <tr><th>Due</th>
      <td><fmt:formatDate value="${lastReview.nextReviewDue}" pattern="yyyy-MM-dd"/></td></tr>
</table>

<%--
  DERIVATION -- how late is this review, and does that matter?

  Computed here, in this file, and nowhere else. The worklist computes something similar in SQL
  with TRUNC and the two round differently.

  The threshold below is the rule: a review more than one full interval late means the member
  has been at this level of care with no authorized clinical justification for that period. The
  banner tells the reviewer. Nothing else in the system reacts to it -- there is no flag, no
  report and no escalation.
--%>
<%
    LocReview last = (LocReview) request.getAttribute("lastReview");
    String lateBanner = null;
    if (last != null && last.getNextReviewDue() != null) {
        long msLate = System.currentTimeMillis() - last.getNextReviewDue().getTime();
        long daysLate = msLate / 86400000L;
        if (daysLate > 0) {
            int interval = last.getReviewIntervalDays();
            if (interval > 0 && daysLate >= interval) {
                lateBanner = "This review is " + daysLate + " day(s) late -- more than one full "
                           + interval + "-day interval. The member has been at "
                           + last.getReviewedLoc() + " without a current authorization for that "
                           + "period. Document the reason.";
            } else {
                lateBanner = "This review is " + daysLate + " day(s) late.";
            }
        }
    }
%>
<% if (lateBanner != null) { %>
  <div class="overdue-banner"><%= lateBanner %></div>
<% } %>

<h2>Review history</h2>
<table class="reviews">
  <tr><th>Seq</th><th>Level</th><th>Units</th><th>Outcome</th><th>Reviewer</th><th>Reviewed</th></tr>
  <c:forEach var="r" items="${reviews}">
    <tr>
      <td>${r.reviewSeq}</td>
      <td>${r.reviewedLoc}</td>
      <td>${r.approvedUnits}</td>
      <td>${r.outcome}</td>
      <td>${r.reviewerUserId} (${r.reviewerCredential})</td>
      <td><fmt:formatDate value="${r.reviewTs}" pattern="yyyy-MM-dd"/></td>
    </tr>
  </c:forEach>
</table>

<h2>Record this review</h2>

<form method="post" action="<c:url value='/auth/${auth.authId}/review'/>">

  <label>Level of care
    <select name="reviewedLoc">
      <%--
        Continue at the current level, or step down one rung. STEPPING UP IS NOT OFFERED.

        A member who deteriorates needs a new authorization, not a continued-stay review, and
        the reason is regulatory rather than technical: an increase in level of care is a new
        determination with its own turnaround clock and its own appeal rights. Expressing that
        as "the dropdown only goes down" is how this system encodes it.
      --%>
      <%
          String[] ladder = { "1.0", "2.1", "2.5", "3.1", "3.5", "3.7", "4.0" };
          String current = last == null ? "1.0" : last.getReviewedLoc();
          int idx = -1;
          for (int i = 0; i < ladder.length; i++) {
              if (ladder[i].equals(current)) { idx = i; break; }
          }
          if (idx < 0) idx = 0;
          out.println("<option value=\"" + ladder[idx] + "\">"
                    + ladder[idx] + " - continue at current level</option>");
          for (int i = idx - 1; i >= 0; i--) {
              out.println("<option value=\"" + ladder[i] + "\">"
                        + ladder[i] + " - step down</option>");
          }
      %>
    </select>
  </label>

  <label>Units approved
    <input type="text" name="approvedUnits" size="5" value="7"/>
    <span class="hint">
      The next review date is computed from the LEVEL, not from this number. A 14-day approval
      at ASAM 3.5 still comes back for review in 7 days.
    </span>
  </label>

  <label>Outcome
    <select name="outcome">
      <option value="APPROVED">Approved &mdash; continue</option>
      <option value="STEPPED_DOWN">Stepped down</option>
      <option value="DISCHARGED">Discharged &mdash; closes the review ladder</option>
      <option value="PENDED">Pended for additional clinical</option>
      <%--
        DENIED is in this list for everyone. ReviewController rejects it for a non-physician
        after the fact -- so a nurse can select it, submit, and be told no.

        It is also the branch where this screen diverges from the determination screen: a
        continued-stay denial recorded here appends a review row and does NOT update
        BH_AUTH.STATUS. The case leaves the worklist looking denied and reads as APPROVED to
        every report. See ReviewController.record().
      --%>
      <option value="DENIED">Denied &mdash; adverse determination (physician only)</option>
    </select>
  </label>

  <button type="submit" class="btn-submit">Record review</button>
</form>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
