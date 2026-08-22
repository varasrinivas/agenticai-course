package com.umlite.casesvc.events;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface OutboxEventRepository extends JpaRepository<OutboxEvent, Long> {

    /** The next batch of unpublished events, oldest first (insertion order). */
    List<OutboxEvent> findTop100ByPublishedAtIsNullOrderByIdAsc();
}
