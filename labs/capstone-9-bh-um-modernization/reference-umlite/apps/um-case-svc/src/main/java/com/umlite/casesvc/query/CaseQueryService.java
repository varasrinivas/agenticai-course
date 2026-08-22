package com.umlite.casesvc.query;

import com.umlite.casesvc.api.CaseResponse;
import com.umlite.casesvc.repo.PriorAuthCaseRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

/**
 * Read-side query service (Phase 5). The single read path used by both the REST controller and the
 * GraphQL resolver. {@code getById} is {@link Cacheable} — cache-aside on Redis (M25): on a miss it
 * loads from Postgres and stores the result; on a hit it skips the DB. Caching is active only when
 * {@code um.cache.enabled=true} (otherwise @EnableCaching is absent and @Cacheable is a no-op), so the
 * service still runs without Redis.
 */
@Service
public class CaseQueryService {

    private final PriorAuthCaseRepository repo;

    public CaseQueryService(PriorAuthCaseRepository repo) {
        this.repo = repo;
    }

    @Cacheable(cacheNames = "case", key = "#id")
    public CaseResponse getById(UUID id) {
        return repo.findById(id).map(CaseResponse::from).orElse(null);
    }

    public List<CaseResponse> all() {
        return repo.findAll().stream().map(CaseResponse::from).toList();
    }

    public List<CaseResponse> byMember(String memberId) {
        return repo.findByMemberId(memberId).stream().map(CaseResponse::from).toList();
    }
}
