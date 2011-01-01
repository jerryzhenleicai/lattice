<%@ page import="org.lattice.G"%>
<%
String name = request.getParameter("name");
G g = new G();
if (name != null) {
    g = new G(name);
}
%>

<%=g%>
