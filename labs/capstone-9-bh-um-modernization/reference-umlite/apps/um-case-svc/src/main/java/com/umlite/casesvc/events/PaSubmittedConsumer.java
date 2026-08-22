package com.umlite.casesvc.events;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.umlite.casesvc.domain.CaseStatus;
import com.umlite.casesvc.domain.PriorAuthCase;
import com.umlite.casesvc.repo.PriorAuthCaseRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

/**
 * Phase 2: consume pa.submitted, create the case, and emit pa.decisioned.
 *
 * Opt-in via {@code um.events.enabled} (so the M09 REST lab and standalone runs are unaffected).
 * At-least-once delivery means this can run twice for one message, so it is <b>idempotent</b> —
 * an already-created case is skipped (M12). The whole handler is {@code @Transactional}; with the
 * outbox enabled (M14) the case change and the outbox row commit atomically.
 */
@Component
public class PaSubmittedConsumer {

    private static final Logger log = LoggerFactory.getLogger(PaSubmittedConsumer.class);

    private final PriorAuthCaseRepository repo;
    private final PaEventsProducer producer;
    private final OutboxEventRepository outbox;
    private final ObjectMapper mapper;

    @Value("${um.events.outbox.enabled:false}")
    private boolean outboxEnabled;

    public PaSubmittedConsumer(PriorAuthCaseRepository repo, PaEventsProducer producer,
                               OutboxEventRepository outbox, ObjectMapper mapper) {
        this.repo = repo;
        this.producer = producer;
        this.outbox = outbox;
        this.mapper = mapper;
    }

    @KafkaListener(
            topics = "${um.events.topics.pa-submitted:pa.submitted}",
            groupId = "um-case-svc",
            autoStartup = "${um.events.enabled:false}")
    @Transactional
    public void onPaSubmitted(String raw) throws Exception {
        EventEnvelope<PaSubmittedPayload> env =
                mapper.readValue(raw, new TypeReference<EventEnvelope<PaSubmittedPayload>>() {});
        PaSubmittedPayload p = env.payload();
        UUID caseId = UUID.fromString(p.caseId());

        if (repo.existsById(caseId)) {
            log.info("pa.submitted duplicate caseId={} — already processed, skipping", caseId);
            return; // idempotent: at-least-once safe
        }

        PriorAuthCase saved = repo.save(new PriorAuthCase(
                caseId, p.memberId(), p.providerId(),
                p.procedureCode(), p.diagnosisCode(), p.requestedUnits()));
        log.info("Created case {} from pa.submitted", saved.getId());

        // Auto-decision stub. Real routing/guideline rules are Track 3 (Camunda DMN).
        saved.transitionTo(CaseStatus.APPROVED);
        repo.save(saved);

        EventEnvelope<PaDecisionedPayload> decided = new EventEnvelope<>(
                UUID.randomUUID().toString(),
                Topics.PA_DECISIONED,
                Instant.now().toString(),
                caseId.toString(),
                1,
                new PaDecisionedPayload(caseId.toString(), "APPROVED", "auto", "stub auto-approval"));

        if (outboxEnabled) {
            // M14 — write the event to the outbox in THIS transaction (atomic with the case change).
            // OutboxPublisher sends it to Kafka afterwards; no dual-write.
            outbox.save(new OutboxEvent(Topics.PA_DECISIONED, caseId.toString(),
                    mapper.writeValueAsString(decided)));
            log.info("Wrote pa.decisioned to outbox caseId={}", caseId);
        } else {
            // M12 — publish directly. Simple, but the DB commit and this send can fail independently.
            producer.publishDecisioned(decided);
            log.info("Published pa.decisioned caseId={} decision=APPROVED", caseId);
        }
    }
}
