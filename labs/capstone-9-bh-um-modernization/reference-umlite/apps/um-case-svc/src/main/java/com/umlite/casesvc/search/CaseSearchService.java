package com.umlite.casesvc.search;

import com.umlite.casesvc.repo.PriorAuthCaseRepository;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Indexing + search over cases (Phase 5 / Track 5, M26). Active only when {@code um.search.enabled=true}
 * (so the service runs without Elasticsearch). {@code reindex} copies the system-of-record cases into
 * the search index; {@code byProcedure} queries the index. In Phase 2 terms, indexing would be driven
 * by the {@code pa.decisioned} event so the index stays in sync.
 */
@Service
@ConditionalOnProperty(name = "um.search.enabled", havingValue = "true")
public class CaseSearchService {

    private final PriorAuthCaseRepository cases;     // system of record (Postgres)
    private final CaseSearchRepository index;        // search store (Elasticsearch)

    public CaseSearchService(PriorAuthCaseRepository cases, CaseSearchRepository index) {
        this.cases = cases;
        this.index = index;
    }

    /** Bulk-index all cases from the source of truth into the search index. */
    public long reindex() {
        List<CaseDocument> docs = cases.findAll().stream().map(CaseDocument::from).toList();
        index.saveAll(docs);
        return docs.size();
    }

    /** Index/update a single case (call this when a case changes). */
    public void index(java.util.UUID caseId) {
        cases.findById(caseId).map(CaseDocument::from).ifPresent(index::save);
    }

    public List<CaseDocument> byProcedure(String procedureCode) {
        return index.findByProcedureCode(procedureCode);
    }

    public List<CaseDocument> byMember(String memberId) {
        return index.findByMemberId(memberId);
    }
}
