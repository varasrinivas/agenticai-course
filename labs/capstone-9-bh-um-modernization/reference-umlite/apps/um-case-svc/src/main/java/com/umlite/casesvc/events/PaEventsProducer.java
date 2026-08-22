package com.umlite.casesvc.events;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

/** Publishes case-service domain events. Keyed by caseId so a case's events stay ordered. */
@Component
public class PaEventsProducer {

    private final KafkaTemplate<String, String> kafka;
    private final ObjectMapper mapper;

    public PaEventsProducer(KafkaTemplate<String, String> kafka, ObjectMapper mapper) {
        this.kafka = kafka;
        this.mapper = mapper;
    }

    /** Publish pa.decisioned, partitioned by the case's correlationId (= caseId). */
    public void publishDecisioned(EventEnvelope<PaDecisionedPayload> event) {
        try {
            kafka.send(Topics.PA_DECISIONED, event.correlationId(), mapper.writeValueAsString(event));
        } catch (Exception e) {
            throw new RuntimeException("Failed to publish pa.decisioned", e);
        }
    }
}
