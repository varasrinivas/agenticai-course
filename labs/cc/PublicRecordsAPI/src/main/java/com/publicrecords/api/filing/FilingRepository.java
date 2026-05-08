package com.publicrecords.api.filing;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FilingRepository extends JpaRepository<Filing, Long> {
    List<Filing> findByState(String state);
}
