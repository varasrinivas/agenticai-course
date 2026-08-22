import { Body, Controller, Post } from '@nestjs/common';
import { CreatePriorAuthDto } from './dto/create-prior-auth.dto';
import { PriorAuthService } from './prior-auth.service';

@Controller('prior-auth')
export class PriorAuthController {
  constructor(private readonly priorAuth: PriorAuthService) {}

  @Post()
  submit(@Body() dto: CreatePriorAuthDto) {
    return this.priorAuth.submit(dto);
  }
}
