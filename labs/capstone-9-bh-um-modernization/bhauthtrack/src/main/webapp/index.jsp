<%--
  The welcome file named in web.xml. It exists only to bounce to the worklist, because
  WorklistController maps "/" as well and the container resolves the welcome file first.

  Two things claim the root URL. They happen to agree.
--%>
<% response.sendRedirect(request.getContextPath() + "/worklist"); %>
