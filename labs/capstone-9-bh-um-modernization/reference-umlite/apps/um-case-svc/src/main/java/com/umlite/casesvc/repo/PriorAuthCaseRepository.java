package com.umlite.casesvc.repo;

import com.umlite.casesvc.domain.PriorAuthCase;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface PriorAuthCaseRepository extends JpaRepository<PriorAuthCase, UUID> {
    List<PriorAuthCase> findByMemberId(String memberId);
}
