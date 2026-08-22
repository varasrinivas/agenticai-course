package com.umlite.casesvc.search;

import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;
import java.util.List;

/**
 * Elasticsearch repository for cases (M26). Spring Data derives queries from method names, just like
 * the JPA repo — but against the search index. Only active when search is enabled
 * (spring.data.elasticsearch.repositories.enabled), so the service runs without Elasticsearch.
 */
public interface CaseSearchRepository extends ElasticsearchRepository<CaseDocument, String> {

    /** Full-text-ish match on procedure code; Keyword filters (member/provider/status) match exactly. */
    List<CaseDocument> findByProcedureCode(String procedureCode);

    List<CaseDocument> findByMemberId(String memberId);

    List<CaseDocument> findByStatus(String status);
}
