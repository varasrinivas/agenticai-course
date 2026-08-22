<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c"   uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%--
  consentAdmin.jsp -- 42 CFR Part 2 consent administration. Admin only.

  EDUCATIONAL MODEL, NOT LEGAL ADVICE. What this screen does is a simplified teaching version of
  the regulation, enough to make the architectural point and not enough to build a compliance
  programme on.

  Unlike every other screen in this application, the role check for this one is in the
  controller rather than in the markup. Two conventions coexist in this codebase; anyone
  inventorying "where does authorization happen" has to find both.

  WHAT IS NOT ON THIS SCREEN is the point of it. There is no accounting of disclosures -- no
  record of who this member's protected record was actually disclosed to, when, or under which
  consent. The consents are here. What was done with them is nowhere.
--%>
<html>
<head>
  <title>Consent &mdash; ${member.lastName}</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>Part 2 consent</h1>

<table class="authhdr">
  <tr><th>Member</th>
      <td>${member.lastName}, ${member.firstName}
          <span class="mid">${member.memberId}</span></td></tr>
  <tr><th>Plan identifier</th>
      <td>
        <c:choose>
          <c:when test="${empty member.planMemberId}">
            <span class="warn">&#9888; none on file</span>
          </c:when>
          <c:otherwise>${member.planMemberId}</c:otherwise>
        </c:choose>
      </td></tr>
  <tr><th>Date of birth</th>
      <td><fmt:formatDate value="${member.dob}" pattern="yyyy-MM-dd"/></td></tr>
</table>

<h2>Consents on file</h2>

<table class="consents">
  <tr>
    <th>Auth</th>
    <th>Recipient</th>
    <th>Type</th>
    <th>Scope</th>
    <th>Purpose</th>
    <th>Signed</th>
    <th>Expires</th>
    <th>Notice</th>
    <th>State</th>
    <th></th>
  </tr>

  <c:forEach var="k" items="${consents}">
    <%--
      STATE, derived in the markup.

      A consent is usable only if it is signed, unexpired and unrevoked. Consent.isUsable()
      implements exactly that in Java -- and this page does not call it. It re-derives the same
      three conditions in JSTL, because the original author found `${k.usable}` did not work
      with the java.util.Date comparison they tried first and worked around it here.

      Two implementations of one rule. They agree today.
    --%>
    <c:set var="revoked"  value="${not empty k.revokedTs}"/>
    <c:set var="expired"  value="${not empty k.expiresTs and k.expiresTs.time lt now}"/>

    <tr class="${revoked or expired ? 'inactive' : ''}">
      <td><a href="<c:url value='/auth/${k.authId}'/>">${k.authId}</a></td>
      <td>${k.recipientName}</td>
      <td>${k.recipientType}</td>

      <%--
        Scope is the field that decides whether the clinical narrative may leave this system.
        FULL_RECORD permits it; the other two do not. Nothing enforces that -- the queue
        payload built in AuthCaseService carries the narrative regardless of what this says.
      --%>
      <td class="scope-${k.scope}">
        ${k.scope}
        <c:if test="${k.scope eq 'FULL_RECORD'}">
          <span class="hint" title="Permits disclosure of the clinical narrative">narrative</span>
        </c:if>
      </td>

      <td>${k.purpose}</td>
      <td><fmt:formatDate value="${k.signedTs}"  pattern="yyyy-MM-dd"/></td>
      <td><fmt:formatDate value="${k.expiresTs}" pattern="yyyy-MM-dd"/></td>

      <td class="${k.redisclosureNoticeSent eq 'Y' ? '' : 'warn'}">
        ${k.redisclosureNoticeSent eq 'Y' ? 'sent' : 'not sent'}
      </td>

      <td>
        <c:choose>
          <c:when test="${revoked}">
            revoked <fmt:formatDate value="${k.revokedTs}" pattern="yyyy-MM-dd"/>
          </c:when>
          <c:when test="${expired}">expired</c:when>
          <c:otherwise>active</c:otherwise>
        </c:choose>
      </td>

      <td>
        <c:if test="${not revoked and not expired}">
          <form method="post" action="<c:url value='/member/${member.memberId}/consent/revoke'/>"
                style="display:inline">
            <input type="hidden" name="consentId" value="${k.consentId}"/>
            <button type="submit" class="btn-revoke">Revoke</button>
          </form>
        </c:if>
        <c:if test="${k.redisclosureNoticeSent ne 'Y'}">
          <form method="post" action="<c:url value='/member/${member.memberId}/consent/notice'/>"
                style="display:inline">
            <input type="hidden" name="consentId" value="${k.consentId}"/>
            <button type="submit" class="btn-notice">Mark notice sent</button>
          </form>
        </c:if>
      </td>
    </tr>
  </c:forEach>
</table>

<c:if test="${empty consents}">
  <p class="empty">No consents on file for this member.</p>
</c:if>

<div class="note">
  <h3>Revocation is prospective</h3>
  <p>
    Revoking a consent records a timestamp. It does not recall anything already disclosed and it
    does not notify the recipient the consent named. This system holds no register of what was
    disclosed under a consent, so the question &ldquo;what went out under the consent I have just
    revoked?&rdquo; cannot be answered here.
  </p>
</div>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
