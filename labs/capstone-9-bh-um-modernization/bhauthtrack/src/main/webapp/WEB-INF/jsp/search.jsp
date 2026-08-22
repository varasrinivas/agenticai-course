<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c"   uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ taglib prefix="fn"  uri="http://java.sun.com/jsp/jstl/functions" %>
<%--
  search.jsp

  READ THIS SCREEN NEXT TO decision.jsp.

  decision.jsp hides the clinical narrative from intake coordinators with
      <c:if test="${sessionScope.roleMask ge 2}">
  and calls that a minimum-necessary control.

  This screen offers a full-text search across every narrative in the database, with no role
  check in the controller and no consent check anywhere. The link to it is hidden below nurse in
  header.jsp -- and hiding a link is not a control, because the URL is /search?mode=clinical&q=.

  The control on one screen is undone by its absence on another. Porting this to a search index
  without adding the missing check reproduces the flaw at higher throughput, and puts a second
  copy of the protected content in a second datastore while doing it.
--%>
<html>
<head>
  <title>Search</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>Search</h1>

<form method="get" action="<c:url value='/search'/>">
  <label>Search by
    <select name="mode">
      <option value="member"   ${mode eq 'member'   ? 'selected' : ''}>Member ID</option>
      <option value="name"     ${mode eq 'name'     ? 'selected' : ''}>Member name</option>
      <option value="clinical" ${mode eq 'clinical' ? 'selected' : ''}>Clinical text</option>
    </select>
  </label>
  <input type="text" name="q" size="40" value="${q}"/>
  <button type="submit">Search</button>
</form>

<%--
  Which identifier matched. The controller tries Bridgeway's key first and the plan's second and
  reports which one hit -- on this screen only. It is the one place in the application where the
  two-identifier problem is visible to a user, and only after a search that happened to use the
  plan's number.
--%>
<c:if test="${not empty matchedOn}">
  <p class="matched">
    Matched on <strong>${matchedOn}</strong>.
    <c:if test="${matchedOn eq 'PLAN_MEMBER_ID'}">
      <span class="hint">
        You searched with the health plan's identifier. Internal screens show Bridgeway's.
      </span>
    </c:if>
    <c:if test="${duplicatePlanIds}">
      <span class="warn">
        &#9888; More than one member has this plan identifier. Only the first is shown.
      </span>
    </c:if>
  </p>
</c:if>

<c:if test="${not empty members}">
  <h2>Members</h2>
  <table class="results">
    <tr><th>Member</th><th>Bridgeway ID</th><th>Plan ID</th><th>DOB</th><th>LOB</th></tr>
    <c:forEach var="m" items="${members}">
      <tr>
        <td>${m.lastName}, ${m.firstName}</td>
        <td><a href="<c:url value='/search?mode=member&q=${m.memberId}'/>">${m.memberId}</a></td>
        <td>
          <c:choose>
            <c:when test="${empty m.planMemberId}">
              <span class="warn" title="Cannot be reconciled with the health plan">&#9888;</span>
            </c:when>
            <c:otherwise>${m.planMemberId}</c:otherwise>
          </c:choose>
        </td>
        <td><fmt:formatDate value="${m.dob}" pattern="yyyy-MM-dd"/></td>
        <td>${m.lineOfBusiness}</td>
      </tr>
    </c:forEach>
  </table>
</c:if>

<c:if test="${not empty auths}">
  <h2>Authorizations <span class="count">(${fn:length(auths)})</span></h2>

  <c:if test="${mode eq 'clinical'}">
    <%--
      The results of a clinical-text search. Note what is NOT shown: the matching text. Someone
      decided in 2011 that showing a snippet would be a step too far, so the results are
      authorization numbers only.

      That is the whole mitigation. The user clicks through to the case, where -- if their role
      mask is 2 or more -- they read the narrative anyway. And they already know the search term
      appears in it, which is itself a disclosure.
    --%>
    <p class="hint">
      Matching text is not displayed. Open a case to read its narrative.
    </p>
  </c:if>

  <table class="results">
    <tr><th>Auth</th><th>Member</th><th>Service</th><th>Dx</th><th>Requested</th>
        <th>Status</th><th>Submitted</th></tr>
    <c:forEach var="a" items="${auths}">
      <tr>
        <td><a href="<c:url value='/auth/${a.authId}'/>">${a.authId}</a></td>
        <td>${a.memberId}</td>
        <td>${a.serviceCode}</td>
        <td>${a.diagnosisCode}</td>
        <td>${a.requestedLoc}</td>
        <td>${a.status}</td>
        <td><fmt:formatDate value="${a.submittedTs}" pattern="yyyy-MM-dd"/></td>
      </tr>
    </c:forEach>
  </table>
</c:if>

<c:if test="${not empty q and empty auths and empty members}">
  <p class="empty">No results.</p>
</c:if>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
