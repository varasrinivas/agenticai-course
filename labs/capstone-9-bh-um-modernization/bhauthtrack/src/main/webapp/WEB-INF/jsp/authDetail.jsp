<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c"   uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ taglib prefix="fn"  uri="http://java.sun.com/jsp/jstl/functions" %>
<%--
  authDetail.jsp -- the case file. Four tabs: request, clinical, review history, audit.

  Tabs are rendered as four divs and switched with the anchor in the URL; there is no
  JavaScript in this application beyond a date picker. All four tabs' content is in the HTML
  regardless of which one is showing.

  THAT IS THE FINDING ON THIS SCREEN. The "clinical" tab is guarded with a role check, but the
  guard controls RENDERING, not RETRIEVAL -- and everything rendered is in the page source. A
  role check that emits content into the response and hides it with a stylesheet is not a
  control. Any port that reproduces "hide the tab" without moving the decision server-side has
  copied the appearance of the rule and not the rule.
--%>
<html>
<head>
  <title>Auth ${auth.authId}</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>Authorization ${auth.authId}</h1>

<c:if test="${provider.part2Program}">
  <div class="part2-banner">
    <strong>42 CFR Part 2 &mdash; protected record.</strong>
    Redisclosure prohibited except as permitted by a consent naming the recipient.
  </div>
</c:if>

<ul class="tabs">
  <li><a href="#request">Request</a></li>
  <c:if test="${sessionScope.roleMask ge 2}"><li><a href="#clinical">Clinical</a></li></c:if>
  <li><a href="#reviews">Review history</a></li>
  <c:if test="${sessionScope.roleMask ge 4}"><li><a href="#audit">Audit</a></li></c:if>
</ul>

<div class="tab" id="request">
  <table class="kv">
    <tr><th>Member</th>
        <td>
          ${member.lastName}, ${member.firstName}
          <span class="mid">${member.memberId}</span>
          <%--
            The plan identifier, and the warning that is the only surfacing of the carve-out
            identity problem anywhere in the application. It is a triangle on one tab of one
            screen. Nothing blocks, nothing alerts, nothing reports.
          --%>
          <c:choose>
            <c:when test="${empty member.planMemberId}">
              <span class="warn" title="No health-plan identifier on file. This authorization
                    cannot be reconciled with the plan.">&#9888; unresolved to plan</span>
            </c:when>
            <c:otherwise>
              <span class="planid">plan ${member.planMemberId}</span>
            </c:otherwise>
          </c:choose>
        </td></tr>
    <tr><th>Date of birth</th>
        <td><fmt:formatDate value="${member.dob}" pattern="yyyy-MM-dd"/></td></tr>
    <tr><th>Line of business</th><td>${member.lineOfBusiness}</td></tr>
    <tr><th>Provider</th>
        <td>${provider.providerName} <span class="npi">NPI ${provider.npi}</span>
            <span class="net">${provider.networkStatus}</span></td></tr>
    <tr><th>Service</th><td>${auth.serviceCode}</td></tr>
    <tr><th>Diagnosis</th><td>${auth.diagnosisCode}</td></tr>
    <tr><th>Requested level of care</th>
        <td>${auth.requestedLoc} for ${auth.requestedUnits} unit(s)</td></tr>
    <tr><th>Urgency</th><td>${auth.urgency}</td></tr>
    <tr><th>Status</th><td class="status-${fn:toLowerCase(auth.status)}">${auth.status}</td></tr>
    <tr><th>Submitted</th>
        <td><fmt:formatDate value="${auth.submittedTs}" pattern="yyyy-MM-dd HH:mm"/></td></tr>
    <tr><th>Decided</th>
        <td>
          <c:choose>
            <c:when test="${empty auth.decidedTs}">&mdash;</c:when>
            <c:otherwise>
              <fmt:formatDate value="${auth.decidedTs}" pattern="yyyy-MM-dd HH:mm"/>
              by ${auth.decidedBy}
            </c:otherwise>
          </c:choose>
        </td></tr>
    <c:if test="${not empty auth.denialReasonCode}">
      <tr><th>Reason code</th><td>${auth.denialReasonCode}</td></tr>
    </c:if>

    <%--
      LEGACY_OVERRIDE surfaced. It is shown but not explained, because nobody knows what it
      means. BHA-2291, 2013, ticket body "per DM request".
    --%>
    <c:if test="${auth.legacyOverride eq 'Y'}">
      <tr class="legacy-ovr">
        <th>Legacy override</th>
        <td>SET &mdash; see BHA-2291. Contact the medical director before acting on this case.</td>
      </tr>
    </c:if>
  </table>
</div>

<%--
  Clinical tab. Nurse and above. See the header comment: this guard controls rendering only,
  and the narrative is in the response either way when the JSP is reached at all.
--%>
<c:if test="${sessionScope.roleMask ge 2}">
  <div class="tab" id="clinical">
    <h3>Clinical narrative</h3>
    <c:choose>
      <c:when test="${empty auth.clinicalNarrative}">
        <p class="empty">
          No narrative. Requests that arrive by EDI carry none &mdash; the 278 has no segment
          for it and no trading partner sends an attachment. Telephone the facility.
        </p>
      </c:when>
      <c:otherwise>
        <pre class="narrative">${auth.clinicalNarrative}</pre>
      </c:otherwise>
    </c:choose>

    <h3>Assessments</h3>
    <table class="assess">
      <tr><th>Instrument</th><th>Dimension</th><th>Score</th><th>Assessed</th></tr>
      <c:forEach var="a" items="${assessments}">
        <tr>
          <td>${a.instrument}</td>
          <td>${empty a.dimension ? '--' : a.dimension}</td>
          <td>${a.score}</td>
          <td><fmt:formatDate value="${a.assessedTs}" pattern="yyyy-MM-dd"/></td>
        </tr>
      </c:forEach>
    </table>

    <h3>Consent on file</h3>
    <c:choose>
      <c:when test="${empty consent}">
        <p class="warn">
          None. <c:if test="${provider.part2Program}">
            <strong>This is a Part 2 program.</strong>
          </c:if>
        </p>
      </c:when>
      <c:otherwise>
        <table class="kv">
          <tr><th>Recipient</th><td>${consent.recipientName} (${consent.recipientType})</td></tr>
          <tr><th>Scope</th><td>${consent.scope}</td></tr>
          <tr><th>Purpose</th><td>${consent.purpose}</td></tr>
          <tr><th>Signed</th>
              <td><fmt:formatDate value="${consent.signedTs}" pattern="yyyy-MM-dd"/></td></tr>
          <tr><th>Expires</th>
              <td><fmt:formatDate value="${consent.expiresTs}" pattern="yyyy-MM-dd"/></td></tr>
          <c:if test="${not empty consent.revokedTs}">
            <tr class="warn"><th>Revoked</th>
                <td><fmt:formatDate value="${consent.revokedTs}" pattern="yyyy-MM-dd"/></td></tr>
          </c:if>
          <tr><th>Redisclosure notice</th>
              <td>${consent.redisclosureNoticeSent eq 'Y' ? 'sent' : 'NOT SENT'}</td></tr>
        </table>
      </c:otherwise>
    </c:choose>
  </div>
</c:if>

<%--
  Review history -- the concurrent-review ladder, which is the thing that has no counterpart in
  medical prior authorization. Sequence 1 is the initial determination; everything after it is a
  continued stay, each row scheduling the next.
--%>
<div class="tab" id="reviews">
  <h3>Review history</h3>
  <table class="reviews">
    <tr>
      <th>Seq</th><th>Level</th><th>Units</th><th>Outcome</th>
      <th>Reviewer</th><th>Credential</th><th>Reviewed</th><th>Next due</th>
    </tr>
    <c:forEach var="r" items="${reviews}">
      <tr>
        <td>${r.reviewSeq}<c:if test="${r.reviewSeq eq 1}"> <span class="hint">initial</span></c:if></td>
        <td>${r.reviewedLoc}</td>
        <td>${r.approvedUnits}</td>
        <td>${r.outcome}</td>
        <td>${r.reviewerUserId}</td>
        <td class="${r.reviewerCredential eq 'UNKNOWN' ? 'warn' : ''}">${r.reviewerCredential}</td>
        <td><fmt:formatDate value="${r.reviewTs}" pattern="yyyy-MM-dd"/></td>
        <td><fmt:formatDate value="${r.nextReviewDue}" pattern="yyyy-MM-dd"/></td>
      </tr>
    </c:forEach>
  </table>

  <c:if test="${auth.status eq 'APPROVED'}">
    <a class="btn" href="<c:url value='/auth/${auth.authId}/review'/>">Record continued stay</a>
  </c:if>
</div>

<%--
  Audit tab. Physician and above.

  The table it reads holds a full copy of the clinical narrative, before and after, for every
  update -- put there in 2011 by the appeals team and never reviewed by privacy. An
  authorization touched twelve times over a residential stay has twelve copies of the protected
  narrative here.

  This page does not show them. It shows status transitions only, which is why nobody has
  noticed what the table contains.
--%>
<c:if test="${sessionScope.roleMask ge 4}">
  <div class="tab" id="audit">
    <h3>Audit</h3>
    <p class="hint">
      Status transitions recorded by TRG_BH_AUTH_AUDIT. Actor attribution is unreliable: the
      trigger reads an Oracle session context set once per request on a pooled connection, so
      some rows are attributed to BHAUTH_APP rather than to a person.
    </p>
    <table class="audit">
      <tr><th>When</th><th>Actor</th><th>Mask</th><th>From</th><th>To</th></tr>
      <c:forEach var="e" items="${auditEvents}">
        <tr>
          <td><fmt:formatDate value="${e.actionTs}" pattern="yyyy-MM-dd HH:mm"/></td>
          <td class="${e.actorUserId eq 'BHAUTH_APP' ? 'warn' : ''}">${e.actorUserId}</td>
          <td>${e.actorRoleMask}</td>
          <td>${e.oldStatus}</td>
          <td>${e.newStatus}</td>
        </tr>
      </c:forEach>
    </table>
  </div>
</c:if>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
