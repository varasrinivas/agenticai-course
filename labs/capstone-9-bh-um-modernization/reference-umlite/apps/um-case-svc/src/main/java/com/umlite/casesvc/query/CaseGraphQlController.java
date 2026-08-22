package com.umlite.casesvc.query;

import com.umlite.casesvc.api.CaseResponse;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.stereotype.Controller;

import java.util.List;
import java.util.UUID;

/**
 * GraphQL data-as-a-service (Phase 5 / Track 5, M24). Read API over the Prior Auth case store, served
 * at /graphql. Each @QueryMapping method backs a field in schema.graphqls; clients request exactly the
 * fields they need. Reads go through CaseQueryService (cache-aside on Redis, M25).
 */
@Controller
public class CaseGraphQlController {

    private final CaseQueryService cases;

    public CaseGraphQlController(CaseQueryService cases) {
        this.cases = cases;
    }

    @QueryMapping
    public List<CaseResponse> cases() {
        return cases.all();
    }

    @QueryMapping(name = "case")
    public CaseResponse caseById(@Argument String id) {
        return cases.getById(UUID.fromString(id));
    }

    @QueryMapping
    public List<CaseResponse> casesByMember(@Argument String memberId) {
        return cases.byMember(memberId);
    }
}
