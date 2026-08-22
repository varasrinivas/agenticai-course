package com.umlite.casesvc.events;

import jakarta.persistence.*;
import java.time.Instant;

/**
 * Transactional outbox row. The case service writes this in the SAME database transaction as the
 * business state change, then {@link OutboxPublisher} publishes unpublished rows to Kafka and marks
 * them published. This removes the dual-write problem (DB commit + Kafka send can't both fail/succeed
 * independently) — the event is published if and only if the transaction committed. See M14.
 */
@Entity
@Table(name = "outbox_event")
public class OutboxEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false) private String topic;
    @Column(name = "event_key", nullable = false) private String eventKey;
    @Column(nullable = false) private String payload;        // the serialized EventEnvelope JSON
    @Column(name = "created_at", nullable = false) private Instant createdAt;
    @Column(name = "published_at") private Instant publishedAt; // null until the poller sends it

    protected OutboxEvent() { } // for JPA

    public OutboxEvent(String topic, String eventKey, String payload) {
        this.topic = topic;
        this.eventKey = eventKey;
        this.payload = payload;
        this.createdAt = Instant.now();
    }

    public void markPublished() {
        this.publishedAt = Instant.now();
    }

    public Long getId() { return id; }
    public String getTopic() { return topic; }
    public String getEventKey() { return eventKey; }
    public String getPayload() { return payload; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getPublishedAt() { return publishedAt; }
}
