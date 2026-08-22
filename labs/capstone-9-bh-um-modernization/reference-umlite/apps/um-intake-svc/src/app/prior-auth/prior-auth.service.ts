import { HttpService } from '@nestjs/axios';
import { Injectable, Logger, ServiceUnavailableException } from '@nestjs/common';
import { randomUUID } from 'crypto';
import { firstValueFrom } from 'rxjs';
import { CreatePriorAuthDto } from './dto/create-prior-auth.dto';
import { KafkaProducerService } from '../events/kafka-producer.service';
import { EventEnvelope, PaSubmittedPayload, Topics } from '../events/pa-events';

@Injectable()
export class PriorAuthService {
  private readonly log = new Logger(PriorAuthService.name);
  private readonly caseSvcBaseUrl =
    process.env.CASE_SVC_BASE_URL ?? 'http://localhost:8081';

  constructor(
    private readonly http: HttpService,
    private readonly kafka: KafkaProducerService,
  ) {}

  /**
   * Phase 2: if eventing is enabled, publish `pa.submitted` and return immediately —
   * the case service consumes it asynchronously, so a submission is never lost when
   * the case service is down. Phase 1 fallback: forward synchronously over REST.
   */
  async submit(dto: CreatePriorAuthDto) {
    if (this.kafka.isEnabled) {
      return this.publishSubmitted(dto);
    }
    return this.forwardOverRest(dto);
  }

  /** Phase 2 — publish the past-tense fact, keyed by caseId for per-case ordering. */
  private async publishSubmitted(dto: CreatePriorAuthDto) {
    const caseId = randomUUID();
    const envelope: EventEnvelope<PaSubmittedPayload> = {
      eventId: randomUUID(),
      eventType: Topics.PA_SUBMITTED,
      occurredAt: new Date().toISOString(),
      correlationId: caseId, // = caseId → the Kafka partition key
      version: 1,
      payload: {
        caseId,
        memberId: dto.memberId,
        providerId: dto.providerId,
        procedureCode: dto.procedureCode,
        diagnosisCode: dto.diagnosisCode,
        requestedUnits: dto.requestedUnits,
      },
    };
    await this.kafka.publish(Topics.PA_SUBMITTED, caseId, envelope);
    this.log.log(`Published pa.submitted member=${dto.memberId} caseId=${caseId}`);
    // Eventual consistency: the case is created by the consumer shortly after.
    return { caseId, status: 'SUBMITTED', mode: 'event' };
  }

  /** Phase 1 — synchronous REST forward to the Spring case service (unchanged). */
  private async forwardOverRest(dto: CreatePriorAuthDto) {
    const url = `${this.caseSvcBaseUrl}/api/cases`;
    this.log.log(`Forwarding PA for member=${dto.memberId} to ${url}`);
    try {
      const res = await firstValueFrom(this.http.post(url, dto));
      return res.data;
    } catch (err) {
      this.log.error(`Case service unreachable: ${(err as Error).message}`);
      throw new ServiceUnavailableException('Case service is unavailable');
    }
  }
}
