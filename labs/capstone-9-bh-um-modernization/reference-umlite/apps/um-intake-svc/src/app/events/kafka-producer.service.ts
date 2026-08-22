import {
  Injectable,
  Logger,
  OnModuleDestroy,
  OnModuleInit,
} from '@nestjs/common';
import { Kafka, logLevel, Producer } from 'kafkajs';

/**
 * Phase 2: a thin KafkaJS producer the intake service uses to publish domain events.
 *
 * It is **opt-in**: unless `EVENTS_ENABLED=true`, the producer never connects and the
 * service keeps working in Phase-1 REST mode (so the M05/M09 labs are unaffected).
 * Broker list comes from `KAFKA_BROKERS` (defaults to the local Redpanda).
 */
@Injectable()
export class KafkaProducerService implements OnModuleInit, OnModuleDestroy {
  private readonly log = new Logger(KafkaProducerService.name);
  private readonly enabled = process.env.EVENTS_ENABLED === 'true';
  private producer?: Producer;

  get isEnabled(): boolean {
    return this.enabled;
  }

  async onModuleInit(): Promise<void> {
    if (!this.enabled) {
      this.log.log(
        'EVENTS_ENABLED!=true — Kafka producer disabled (Phase-1 REST mode)',
      );
      return;
    }
    const brokers = (process.env.KAFKA_BROKERS ?? 'localhost:9092').split(',');
    const kafka = new Kafka({
      clientId: 'um-intake-svc',
      brokers,
      logLevel: logLevel.NOTHING,
    });
    this.producer = kafka.producer();
    await this.producer.connect();
    this.log.log(`Kafka producer connected to ${brokers.join(',')}`);
  }

  async onModuleDestroy(): Promise<void> {
    await this.producer?.disconnect();
  }

  /** Publish a JSON event to `topic`, partitioned by `key` (use the caseId). */
  async publish(topic: string, key: string, value: unknown): Promise<void> {
    if (!this.producer) {
      throw new Error('Kafka producer not initialized (EVENTS_ENABLED!=true)');
    }
    await this.producer.send({
      topic,
      messages: [{ key, value: JSON.stringify(value) }],
    });
    this.log.log(`Published ${topic} key=${key}`);
  }
}
