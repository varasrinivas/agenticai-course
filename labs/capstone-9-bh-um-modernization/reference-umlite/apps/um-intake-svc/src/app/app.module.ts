import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { HttpModule } from '@nestjs/axios';
import { HealthController } from './health/health.controller';
import { PriorAuthController } from './prior-auth/prior-auth.controller';
import { PriorAuthService } from './prior-auth/prior-auth.service';
import { EventsModule } from './events/events.module';

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true }), HttpModule, EventsModule],
  controllers: [HealthController, PriorAuthController],
  providers: [PriorAuthService],
})
export class AppModule {}
