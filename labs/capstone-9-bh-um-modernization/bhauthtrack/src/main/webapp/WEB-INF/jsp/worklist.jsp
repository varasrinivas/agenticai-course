<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c"   uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ taglib prefix="fn"  uri="http://java.sun.com/jsp/jstl/functions" %>
<%--
  worklist.jsp -- the home screen and the work-distribution mechanism.

  THE SECOND ROLE FILTER LIVES HERE.

  WorklistDao.forReviewer() already filtered by role in SQL. This page filters AGAIN, and by a
  different rule: the SQL hides cases a nurse cannot act on, while the markup below hides the
  action link on cases whose diagnosis requires a specialty the viewer lacks -- something the
  SQL knows nothing about.

  Neither filter is a superset of the other. "What work is mine?" has two answers in this
  system depending on which layer you ask, and a port has to pick one before it can move it.

  There is also no claiming. Two reviewers can open the same row; the second save wins.
--%>
<html>
<head>
  <title>Worklist</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>Worklist</h1>

<p class="summary">
  ${fn:length(items)} case(s).
  <c:set var="overdueCount" value="0"/>
  <c:forEach var="i" items="${items}">
    <c:if test="${i.daysUntilDue lt 0}"><c:set var="overdueCount" value="${overdueCount + 1}"/></c:if>
  </c:forEach>
  <c:if test="${overdueCount gt 0}">
    <span class="overdue">${overdueCount} overdue.</span>
  </c:if>
</p>

<table class="worklist">
  <tr>
    <th>Auth</th>
    <th>Member</th>
    <th>Dx</th>
    <th>Requested</th>
    <th>Current</th>
    <th>Status</th>
    <th>Review due</th>
    <th>Action</th>
  </tr>

  <c:forEach var="i" items="${items}">
    <tr class="${i.daysUntilDue lt 0 ? 'overdue' : (i.urgency eq 'EXPEDITED' ? 'expedited' : '')}">

      <td><a href="<c:url value='/auth/${i.authId}'/>">${i.authId}</a></td>

      <%--
        Member column. Note that it shows the BRIDGEWAY identifier -- reviewers know it as "the
        member number" and would not recognise the plan's. Every screen in this application
        shows this one, which is part of why the distinction is invisible to the people who use
        the system daily.
      --%>
      <td>
        ${i.memberLastName}
        <span class="mid">${i.memberId}</span>
        <c:if test="${i.part2Program}">
          <span class="p2" title="42 CFR Part 2 protected record">P2</span>
        </c:if>
      </td>

      <td>${i.diagnosisCode}</td>
      <td>${i.requestedLoc}</td>
      <td>${empty i.currentLoc ? '--' : i.currentLoc}</td>

      <td>
        ${i.status}
        <c:if test="${i.reviewSeq gt 1}">
          <span class="seq" title="Continued stay, review ${i.reviewSeq}">CS ${i.reviewSeq}</span>
        </c:if>
      </td>

      <td class="${i.daysUntilDue lt 0 ? 'overdue' : (i.daysUntilDue le 1 ? 'duesoon' : '')}">
        <c:choose>
          <c:when test="${empty i.nextReviewDue}">--</c:when>
          <c:when test="${i.daysUntilDue lt 0}">OVERDUE ${-i.daysUntilDue}d</c:when>
          <c:otherwise>
            <fmt:formatDate value="${i.nextReviewDue}" pattern="MM/dd"/>
            (${i.daysUntilDue}d)
          </c:otherwise>
        </c:choose>
      </td>

      <%--
        RULE IN A VIEW -- WHICH ACTION, AND WHETHER THERE IS ONE AT ALL.

        Three separate business rules are expressed by this cell, and none of them exists
        anywhere else:

          1. Continued stay routes to /review; an initial determination routes to /decide.
             The distinction is reviewSeq > 1, computed in SQL and applied here.

          2. A case pended for an adverse determination offers no action to a non-physician.
             (The SQL already excluded those rows for a nurse -- so this branch is unreachable
             for nurses and IS reachable for an admin, whose mask is 32 and who passes 'ge 4'.)

          3. A substance-use diagnosis pended for denial offers no action to a physician who is
             not addiction-medicine. THIS RULE EXISTS ONLY HERE AND IN decision.jsp. The SQL
             does not know about it, so those rows sit on every physician's worklist -- visible,
             counted in the totals, and unactionable by most of the people looking at them.
      --%>
      <td>
        <c:choose>
          <c:when test="${i.status eq 'PENDED' and sessionScope.roleMask lt 4}">
            <span class="noaction">Physician review</span>
          </c:when>

          <c:when test="${i.status eq 'PENDED'
                          and fn:startsWith(i.diagnosisCode, 'F1')
                          and sessionScope.roleMask lt 16}">
            <span class="noaction">Addiction medicine</span>
          </c:when>

          <c:when test="${i.reviewSeq gt 1}">
            <a class="btn" href="<c:url value='/auth/${i.authId}/review'/>">Continued stay</a>
          </c:when>

          <c:otherwise>
            <a class="btn" href="<c:url value='/auth/${i.authId}/decide'/>">Review</a>
          </c:otherwise>
        </c:choose>
      </td>
    </tr>
  </c:forEach>
</table>

<c:if test="${empty items}">
  <p class="empty">Nothing on your worklist.</p>
</c:if>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
