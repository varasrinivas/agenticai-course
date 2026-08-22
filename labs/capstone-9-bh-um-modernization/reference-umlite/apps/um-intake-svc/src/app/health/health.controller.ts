import { Controller, Get } from '@nestjs/common';

@Controller('health')
export class HealthController {
  @Get()
  check() {
    return { status: 'ok', service: 'um-intake-svc', ts: new Date().toISOString() };
  }
}
