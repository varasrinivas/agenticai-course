<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c"   uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ taglib prefix="fn"  uri="http://java.sun.com/jsp/jstl/functions" %>
<%@ page import="com.bridgeway.bhauth.domain.Auth" %>
<%@ page import="com.bridgeway.bhauth.domain.LocReview" %>
<%@ page import="java.util.Date" %>
<%--
  decision.jsp -- the determination screen.

  MAINTENANCE NOTE (2014): the role checks below are the ONLY thing standing between a nurse
  reviewer and the deny button on most deployments. AuthCaseService.issueDenial() re-checks, but
  that was added after the fact and there are two other call paths (the batch importer and the
  SOAP endpoint) that do not go through it. Treat this file as security-relevant.

  DO NOT "clean up" the scriptlets at the bottom without reading them. The
  continued-stay-due calculation and the expedited-clock calculation exist nowhere else in the
  codebase. Reporting reimplemented them in Crystal and the two have disagreed since 2015.
--%>
<html>
<head>
  <title>Determination &mdash; Auth ${auth.authId}</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>Determination</h1>

<table class="authhdr">
  <tr><th>Authorization</th><td>${auth.authId}</td></tr>
  <tr><th>Member</th><td>${auth.memberId}</td></tr>
  <tr><th>Requested level of care</th><td>${auth.requestedLoc}</td></tr>
  <tr><th>Service</th><td>${auth.serviceCode}</td></tr>
  <tr><th>Diagnosis</th><td>${auth.diagnosisCode}</td></tr>
  <tr><th>Urgency</th><td>${auth.urgency}</td></tr>
  <tr><th>Status</th><td>${auth.status}</td></tr>
</table>

<%--
  RULE IN A VIEW #1 -- Part 2 banner.
  If the requesting provider is a federally assisted SUD program, the record carries a
  redisclosure restriction. This banner is the only place in the application that tells the
  reviewer that. There is no corresponding server-side control.
--%>
<c:if test="${provider.part2Program}">
  <div class="part2-banner">
    <strong>42 CFR Part 2 &mdash; protected record.</strong>
    This information has been disclosed from records protected by federal confidentiality rules.
    Redisclosure is prohibited except as permitted by a consent that names the recipient.
    <c:choose>
      <c:when test="${consent.scope == 'FULL_RECORD'}">
        Consent on file: full record, recipient <em>${consent.recipientName}</em>,
        expires <fmt:formatDate value="${consent.expiresTs}" pattern="yyyy-MM-dd"/>.
      </c:when>
      <c:when test="${consent.scope == 'AUTH_DECISION_ONLY'}">
        Consent on file covers the <strong>determination only</strong> &mdash;
        do not include clinical narrative in any correspondence.
      </c:when>
      <c:otherwise>
        <strong class="warn">No usable consent on file. Do not disclose.</strong>
      </c:otherwise>
    </c:choose>
  </div>
</c:if>

<%--
  RULE IN A VIEW #2 -- narrative visibility.
  Intake coordinators are non-clinical and must not read the clinical narrative. This is a
  minimum-necessary control implemented as a template conditional.
--%>
<c:if test="${sessionScope.roleMask ge 2}">
  <div class="narrative">
    <h3>Clinical narrative</h3>
    <pre>${auth.clinicalNarrative}</pre>
  </div>
</c:if>

<h2>Rule evaluation</h2>
<table class="rulepath">
  <tr><th>Engine outcome</th><td>${decision.outcome}</td></tr>
  <tr><th>Granted level of care</th><td>${decision.grantedLoc}</td></tr>
  <tr><th>Granted units</th><td>${decision.grantedUnits}</td></tr>
  <tr><th>Review interval (days)</th><td>${decision.intervalDays}</td></tr>
  <tr><th>Rule path</th><td><code>${decision.rulePath}</code></td></tr>
</table>

<h2>Actions</h2>

<form method="post" action="<c:url value='/auth/${auth.authId}/decide'/>">

  <%--
    RULE IN A VIEW #3 -- THE ROLE RULE.

    A nurse may approve. A nurse may NEVER deny. Only a physician may issue an adverse
    determination, and for substance-use or psychiatric level-of-care the physician is expected
    to be same-specialty.

    This is separation of duties required by accreditation, expressed as three nested JSTL
    conditionals. It is not styling. An agent that ports this file as markup produces a screen
    where every reviewer sees the deny button.
  --%>

  <c:if test="${sessionScope.roleMask ge 2}">
    <button type="submit" name="action" value="APPROVE" class="btn-approve">
      Approve
    </button>
    <button type="submit" name="action" value="PEND" class="btn-pend">
      Pend for additional clinical
    </button>
  </c:if>

  <c:choose>
    <%-- bit 4 = BH_MD. Bitwise test written as a range because JSTL has no bitwise operator. --%>
    <c:when test="${sessionScope.roleMask ge 4}">
      <c:choose>
        <%-- SUD diagnoses are F10-F19. Addiction-medicine reviewer required. --%>
        <c:when test="${fn:startsWith(auth.diagnosisCode, 'F1')}">
          <c:choose>
            <c:when test="${sessionScope.roleMask ge 16}">
              <button type="submit" name="action" value="DENY" class="btn-deny">
                Deny (addiction medicine)
              </button>
            </c:when>
            <c:otherwise>
              <p class="note">
                Adverse determination on a substance-use diagnosis requires an
                addiction-medicine reviewer. Route to peer review.
              </p>
              <button type="submit" name="action" value="PEER_ROUTE" class="btn-route">
                Route to peer review
              </button>
            </c:otherwise>
          </c:choose>
        </c:when>
        <c:otherwise>
          <button type="submit" name="action" value="DENY" class="btn-deny">
            Deny
          </button>
        </c:otherwise>
      </c:choose>
    </c:when>
    <c:otherwise>
      <p class="note">
        Approval only. Adverse determinations require a physician reviewer.
      </p>
    </c:otherwise>
  </c:choose>

  <input type="hidden" name="authId" value="${auth.authId}"/>
</form>

<%--
  SCRIPTLET-ONLY DERIVATIONS.

  These two values are computed here and nowhere else in the application. They are displayed to
  the reviewer and they drive the reviewer's behaviour, but no service, no DAO and no database
  column holds them.

  Anyone porting this screen has to notice that these are business rules wearing a costume.
--%>
<%
    Auth a = (Auth) request.getAttribute("auth");
    LocReview lastReview = (LocReview) request.getAttribute("lastReview");

    // DERIVATION #1 -- continued-stay countdown.
    // A residential authorization not re-reviewed inside its interval is out of compliance.
    // The worklist sorts on this. It is recomputed on every page render.
    String dueLabel = "n/a";
    String dueClass = "";
    if (lastReview != null && lastReview.getNextReviewDue() != null) {
        long msLeft = lastReview.getNextReviewDue().getTime() - System.currentTimeMillis();
        long daysLeft = msLeft / 86400000L;
        dueLabel = daysLeft + " day(s)";
        if (daysLeft < 0)      { dueClass = "overdue"; dueLabel = "OVERDUE by " + (-daysLeft) + " day(s)"; }
        else if (daysLeft <= 1){ dueClass = "duesoon"; }
    }

    // DERIVATION #2 -- regulatory turnaround clock.
    // Expedited requests get 72 hours; standard requests get 14 calendar days. Missing the
    // deadline can force an automatic approval depending on line of business. This is the only
    // implementation of that rule in the codebase.
    String tatLabel = "n/a";
    String tatClass = "";
    if (a != null && a.getSubmittedTs() != null && a.getDecidedTs() == null) {
        int allowedHours = "EXPEDITED".equals(a.getUrgency()) ? 72 : 336;
        long elapsedH = (System.currentTimeMillis() - a.getSubmittedTs().getTime()) / 3600000L;
        long remainingH = allowedHours - elapsedH;
        tatLabel = remainingH + "h remaining of " + allowedHours + "h";
        if (remainingH < 0)       { tatClass = "overdue"; tatLabel = "TAT BREACHED"; }
        else if (remainingH < 24) { tatClass = "duesoon"; }
    }
%>

<h2>Clocks</h2>
<table class="clocks">
  <tr>
    <th>Next continued-stay review</th>
    <td class="<%= dueClass %>"><%= dueLabel %></td>
  </tr>
  <tr>
    <th>Regulatory turnaround</th>
    <td class="<%= tatClass %>"><%= tatLabel %></td>
  </tr>
</table>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
