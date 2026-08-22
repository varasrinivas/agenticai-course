package com.umlite.casesvc.events;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * Common event envelope — the Java mirror of EventEnvelope&lt;T&gt; in @um-lite/events.
 * Unknown fields are ignored so the producer can add envelope metadata without breaking
 * this consumer (forward-compatible — see M13).
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record EventEnvelope<T>(
        String eventId,
        String eventType,
        String occurredAt,
        String correlationId,   // = caseId
        int version,
        T payload
) { }
