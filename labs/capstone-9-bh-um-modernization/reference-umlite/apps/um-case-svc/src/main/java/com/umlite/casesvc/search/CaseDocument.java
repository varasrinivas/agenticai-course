package com.umlite.casesvc.search;

import com.umlite.casesvc.domain.PriorAuthCase;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;

/**
 * Search projection of a Prior Auth case (Phase 5 / Track 5, M26). Indexed into Elasticsearch so it
 * can be searched by free text + filtered — a different store, optimized for search, kept in sync from
 * the case data. Distinct from the JPA entity (PriorAuthCase) and the API DTO (CaseResponse).
 */
@Document(indexName = "cases")
public class CaseDocument {

    @Id
    private String caseId;

    @Field(type = FieldType.Keyword)
    private String memberId;

    @Field(type = FieldType.Keyword)
    private String providerId;

    @Field(type = FieldType.Text)
    private String procedureCode;

    @Field(type = FieldType.Text)
    private String diagnosisCode;

    @Field(type = FieldType.Keyword)
    private String status;

    public CaseDocument() { }

    public static CaseDocument from(PriorAuthCase c) {
        CaseDocument d = new CaseDocument();
        d.caseId = c.getId().toString();
        d.memberId = c.getMemberId();
        d.providerId = c.getProviderId();
        d.procedureCode = c.getProcedureCode();
        d.diagnosisCode = c.getDiagnosisCode();
        d.status = c.getStatus().name();
        return d;
    }

    public String getCaseId() { return caseId; }
    public String getMemberId() { return memberId; }
    public String getProviderId() { return providerId; }
    public String getProcedureCode() { return procedureCode; }
    public String getDiagnosisCode() { return diagnosisCode; }
    public String getStatus() { return status; }
}
