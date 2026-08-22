package com.umlite.casesvc.workflow;

import com.umlite.casesvc.events.EventEnvelope;
import com.umlite.casesvc.events.PaDecisionedPayload;
import com.umlite.casesvc.events.PaEventsProducer;
import com.umlite.casesvc.events.Topics;
import org.camunda.bpm.client.spring.annotation.ExternalTaskSubscription;
import org.camunda.bpm.client.task.ExternalTask;
import org.camunda.bpm.client.task.ExternalTaskHandler;
import org.camunda.bpm.client.task.ExternalTaskService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.UUID;

/**
 * Phase 3 (Track 3) external-task worker. The Camunda engine owns the Prior Auth process; this
 * service is a <b>worker</b> that fetches-and-locks the "notify-decision" external task, does the
 * work (publish pa.decisioned), and completes the task — the job/worker pattern (M16).
 *
 * Only active when {@code um.workflow.enabled=true}, so the case service still boots and runs in
 * REST/event mode without Camunda. Process orchestration replaces the inline auto-decision (M18).
 */
@Component
@ConditionalOnProperty(name = "um.workflow.enabled", havingValue = "true")
@ExternalTaskSubscription(topicName = "notify-decision")
public class NotifyDecisionWorker implements ExternalTaskHandler {

    private static final Logger log = LoggerFactory.getLogger(NotifyDecisionWorker.class);

    private final PaEventsProducer producer;

    public NotifyDecisionWorker(PaEventsProducer producer) {
        this.producer = producer;
    }

    @Override
    public void execute(ExternalTask task, ExternalTaskService externalTaskService) {
        String caseId = task.getVariable("caseId");
        String decision = task.getVariable("decision"); // set by the DMN business-rule task

        log.info("Worker handling notify-decision caseId={} decision={}", caseId, decision);

        producer.publishDecisioned(new EventEnvelope<>(
                UUID.randomUUID().toString(),
                Topics.PA_DECISIONED,
                Instant.now().toString(),
                caseId,
                1,
                new PaDecisionedPayload(caseId, decision, "camunda", "decided by Prior Auth process")));

        // Tell the engine the job is done so the process can move to the next step.
        externalTaskService.complete(task);
    }
}
