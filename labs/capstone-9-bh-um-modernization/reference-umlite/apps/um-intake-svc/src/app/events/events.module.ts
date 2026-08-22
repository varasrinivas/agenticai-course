import { Module } from '@nestjs/common';
import { KafkaProducerService } from './kafka-producer.service';

/** Phase-2 eventing wiring. Exports the Kafka producer for feature services to use. */
@Module({
  providers: [KafkaProducerService],
  exports: [KafkaProducerService],
})
export class EventsModule {}
