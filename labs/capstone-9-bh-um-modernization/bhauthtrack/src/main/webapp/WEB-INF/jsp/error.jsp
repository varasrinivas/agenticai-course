<%@ page language="java" contentType="text/html; charset=UTF-8" isErrorPage="true" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%--
  error.jsp

  Note what this prints: the exception message, verbatim, to the browser.

  Several of the messages it can print carry clinical content -- AuthDao.searchNarrative()
  failing on a malformed CLOB predicate puts the search term in the message, and a constraint
  violation on BH_LOC_REVIEW puts the authorization number and reviewer in it. The page has
  been like this since 4.0 and the reasoning at the time was that reviewers needed something
  concrete to quote to the help desk.
--%>
<html>
<head>
  <title>Error</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>Something went wrong</h1>

<div class="errorbox">
  <p>The action could not be completed. Nothing was saved.</p>
  <p class="detail"><%= exception == null ? "" : exception.getMessage() %></p>
  <p class="hint">
    Quote the message above to the help desk. Do not include member details in the ticket.
  </p>
</div>

<p><a href="<c:url value='/worklist'/>">Back to the worklist</a></p>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
