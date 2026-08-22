package com.umlite.casesvc.api;

import com.umlite.casesvc.domain.PriorAuthCase;
import com.umlite.casesvc.repo.PriorAuthCaseRepository;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;

@RestController
@RequestMapping("/api/cases")
public class CaseController {

    private final PriorAuthCaseRepository repo;

    public CaseController(PriorAuthCaseRepository repo) {
        this.repo = repo;
    }

    /** Create a new Prior Auth case. Phase 2: also emit pa.submitted to Kafka. */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public CaseResponse create(@Valid @RequestBody CreateCaseRequest req) {
        PriorAuthCase saved = repo.save(new PriorAuthCase(
                req.memberId(), req.providerId(), req.procedureCode(),
                req.diagnosisCode(), req.requestedUnits()));
        return CaseResponse.from(saved);
    }

    @GetMapping("/{id}")
    public CaseResponse getById(@PathVariable UUID id) {
        return repo.findById(id)
                .map(CaseResponse::from)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Case not found"));
    }
}
