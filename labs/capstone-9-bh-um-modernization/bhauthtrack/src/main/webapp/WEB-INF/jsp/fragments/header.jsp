<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%--
  Shared page header. Included by every screen.

  The navigation below is role-filtered in JSTL. That is the only thing preventing an intake
  coordinator reaching /member/{id}/consent -- ConsentController checks the role too, so this
  one is cosmetic. It is NOT cosmetic for /search, which has no server-side check at all: the
  clinical-text search is reachable by URL by anyone, and hiding the link is the whole control.

  See SearchController for what that means.
--%>
<div class="hdr">
  <span class="app">BHAuthTrack <span class="ver">4.2</span></span>
  <span class="env">${initParam['bhauth.env']}</span>

  <ul class="nav">
    <li><a href="<c:url value='/worklist'/>">Worklist</a></li>

    <c:if test="${sessionScope.roleMask ge 1}">
      <li><a href="<c:url value='/auth/new'/>">New request</a></li>
    </c:if>

    <%-- Clinical search. Hidden below nurse. Not guarded on the server. --%>
    <c:if test="${sessionScope.roleMask ge 2}">
      <li><a href="<c:url value='/search'/>">Search</a></li>
    </c:if>

    <%-- Admin only. ConsentController re-checks. --%>
    <c:if test="${sessionScope.roleMask ge 32}">
      <li><a href="<c:url value='/admin/users'/>">Users</a></li>
    </c:if>
  </ul>

  <span class="whoami">
    ${sessionScope.userId}
    <c:choose>
      <c:when test="${sessionScope.credential eq 'UNKNOWN'}">
        <%-- The directory title did not map to anything this system understands. The user can
             still work; BH_LOC_REVIEW.REVIEWER_CREDENTIAL will record 'UNKNOWN', which defeats
             the 2015 audit finding that column was added for. --%>
        <span class="warn" title="Credential not recognised in the directory">(credential
        unknown)</span>
      </c:when>
      <c:otherwise>
        <span class="cred">${sessionScope.credential}</span>
      </c:otherwise>
    </c:choose>
  </span>
</div>

<c:if test="${not empty error}">
  <div class="errorbox">${error}</div>
</c:if>
