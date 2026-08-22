<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="c"    uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="form" uri="http://www.springframework.org/tags/form" %>
<%--
  authSubmit.jsp -- intake.

  ONE FORM, THREE ENTITIES. The authorization, the six ASAM dimension scores and the 42 CFR
  Part 2 consent are collected together and posted together, because AuthCaseService writes them
  together in one transaction. The shape of this form IS the shape of that transaction.

  That is worth dwelling on before splitting the backend into services. If intake and case
  become separate deployables, this one POST becomes two or three calls that can partially fail,
  and the form has to grow a concept it does not have today: a draft.

  VALIDATION: there is none, here or in the controller. The database CHECK constraints are the
  validation layer. Note especially that the dimension inputs are type="text" with no range
  check -- a dimension-1 score of 40 walks the ladder straight to ASAM 4.0.
--%>
<html>
<head>
  <title>New authorization request</title>
  <link rel="stylesheet" href="<c:url value='/css/bhauth.css'/>"/>
</head>
<body>

<jsp:include page="fragments/header.jsp"/>

<h1>New authorization request</h1>

<form:form method="post" action="${pageContext.request.contextPath}/auth" modelAttribute="auth">

  <fieldset>
    <legend>Request</legend>

    <label>Member ID
      <form:input path="memberId" size="24"/>
      <span class="hint">Bridgeway member number (not the health plan's).</span>
    </label>

    <label>Provider ID
      <form:input path="bridgewayProvId" size="24"/>
    </label>

    <label>Service code
      <form:input path="serviceCode" size="10"/>
      <span class="hint">
        CPT 90791 90792 90832 90834 90837 90853 &middot; ABA 97151&ndash;97158 &middot;
        HCPCS H0015 H0018 H0019 H2036 S9480
      </span>
    </label>

    <label>Diagnosis (ICD-10)
      <form:input path="diagnosisCode" size="10"/>
    </label>

    <label>Requested level of care
      <form:select path="requestedLoc">
        <form:option value="1.0" label="1.0 - Outpatient"/>
        <form:option value="2.1" label="2.1 - Intensive outpatient (IOP)"/>
        <form:option value="2.5" label="2.5 - Partial hospitalization (PHP)"/>
        <form:option value="3.1" label="3.1 - Clinically managed low-intensity residential"/>
        <form:option value="3.5" label="3.5 - Clinically managed high-intensity residential"/>
        <form:option value="3.7" label="3.7 - Medically monitored intensive inpatient"/>
        <form:option value="4.0" label="4.0 - Medically managed intensive inpatient"/>
      </form:select>
    </label>

    <label>Requested units
      <form:input path="requestedUnits" size="5"/>
      <span class="hint">Days for residential and inpatient; sessions for outpatient.</span>
    </label>

    <label>Urgency
      <form:select path="urgency">
        <form:option value="STANDARD"  label="Standard (14 calendar days)"/>
        <form:option value="EXPEDITED" label="Expedited (72 hours)"/>
      </form:select>
    </label>
  </fieldset>

  <fieldset>
    <legend>Clinical narrative</legend>
    <p class="hint">
      The clinical justification a reviewer will read. When the requesting provider is a
      federally assisted substance-use-disorder treatment program this text is protected under
      42 CFR Part 2.
    </p>
    <form:textarea path="clinicalNarrative" rows="10" cols="80"/>
  </fieldset>

  <fieldset>
    <legend>ASAM dimensions</legend>
    <p class="hint">
      Score each dimension 0&ndash;4. These are the inputs to the level-of-care engine; the
      engine reads them from the database after this form is saved.
    </p>
    <table class="dims">
      <tr><td>1. Acute intoxication / withdrawal potential</td>
          <td><input type="text" name="dim1" size="2" value="0"/></td></tr>
      <tr><td>2. Biomedical conditions and complications</td>
          <td><input type="text" name="dim2" size="2" value="0"/></td></tr>
      <tr><td>3. Emotional / behavioral / cognitive conditions</td>
          <td><input type="text" name="dim3" size="2" value="0"/></td></tr>
      <tr><td>4. Readiness to change
              <span class="hint">A LOW score reduces the case for residential.</span></td>
          <td><input type="text" name="dim4" size="2" value="0"/></td></tr>
      <tr><td>5. Relapse / continued use potential</td>
          <td><input type="text" name="dim5" size="2" value="0"/></td></tr>
      <tr><td>6. Recovery / living environment</td>
          <td><input type="text" name="dim6" size="2" value="0"/></td></tr>
    </table>
  </fieldset>

  <%--
    Consent, on the intake form.

    Captured for EVERY request, not only Part 2 ones, because BH_PROVIDER.IS_PART2_PROGRAM was
    backfilled from a spreadsheet in 2014 and has been wrong before. Over-capturing is the
    mitigation for an unreliable flag.

    Note the defaults: recipient defaults to the plan and scope defaults to AUTH_DECISION_ONLY,
    both applied in AuthController.buildConsent() rather than here. A consent submitted with
    every field left blank is still a valid row.
  --%>
  <fieldset>
    <legend>42 CFR Part 2 consent</legend>

    <label>Recipient
      <input type="text" name="consentRecipient" size="60"/>
      <span class="hint">
        A Part 2 consent names its recipient. Blank defaults to the health plan.
      </span>
    </label>

    <label>Scope
      <select name="consentScope">
        <option value="AUTH_DECISION_ONLY">Determination only</option>
        <option value="DATES_OF_SERVICE_ONLY">Dates of service only</option>
        <option value="FULL_RECORD">Full record (includes clinical narrative)</option>
      </select>
    </label>

    <label>Purpose
      <input type="text" name="consentPurpose" size="60"/>
    </label>
  </fieldset>

  <button type="submit" class="btn-submit">Submit request</button>

  <p class="warn-atomic">
    If any part of this request cannot be saved, none of it is saved and you will be asked to
    resubmit. There is no draft.
  </p>

</form:form>

<jsp:include page="fragments/footer.jsp"/>

</body>
</html>
