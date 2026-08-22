import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app/app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // Reject unknown fields and coerce types from the DTOs.
  app.useGlobalPipes(
    new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }),
  );
  app.enableCors(); // the Angular UI calls this service directly in Phase 1
  const port = process.env.INTAKE_SVC_PORT ?? 3000;
  await app.listen(port);
  // eslint-disable-next-line no-console
  console.log(`um-intake-svc listening on http://localhost:${port}`);
}
bootstrap();
