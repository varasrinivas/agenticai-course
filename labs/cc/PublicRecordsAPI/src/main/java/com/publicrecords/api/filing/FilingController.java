package com.publicrecords.api.filing;

import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/filings")
public class FilingController {

    private final FilingRepository repository;

    public FilingController(FilingRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public List<Filing> list(@RequestParam(required = false) String state) {
        return state == null ? repository.findAll() : repository.findByState(state);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Filing> findById(@PathVariable Long id) {
        return repository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
