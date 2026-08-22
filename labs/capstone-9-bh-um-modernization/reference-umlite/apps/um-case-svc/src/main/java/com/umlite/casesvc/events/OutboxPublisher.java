package com.umlite.casesvc.events;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Polls the outbox table and publishes unpublished rows to Kafka, then marks them published.
 *
 * Decoupling the Kafka send from the business transaction is what removes the dual-write hazard:
 * the consumer only commits the case + outbox row to the DB (one transaction); this poller does the
 * (separately-failable) network publish. Delivery is at-least-once — a crash after send() but before
 * the published_at flush re-publishes the row next tick, which is safe because consumers are
 * idempotent (M12 / M14). Active only when {@code um.events.outbox.enabled=true}.
 */
@Component
public class OutboxPublisher {

    private static final Logger log = LoggerFactory.getLogger(OutboxPublisher.class);

    private final OutboxEventRepository outbox;
    private final KafkaTemplate<String, String> kafka;

    @Value("${um.events.outbox.enabled:false}")
    private boolean enabled;

    public OutboxPublisher(OutboxEventRepository outbox, KafkaTemplate<String, String> kafka) {
        this.outbox = outbox;
        this.kafka = kafka;
    }

    @Scheduled(fixedDelayString = "${um.events.outbox.poll-ms:1000}")
    @Transactional
    public void publishPending() {
        if (!enabled) {
            return;
        }
        List<OutboxEvent> batch = outbox.findTop100ByPublishedAtIsNullOrderByIdAsc();
        for (OutboxEvent e : batch) {
            kafka.send(e.getTopic(), e.getEventKey(), e.getPayload());
            e.markPublished(); // flushed when this transaction commits
            log.info("Outbox published id={} topic={} key={}", e.getId(), e.getTopic(), e.getEventKey());
        }
    }
}
