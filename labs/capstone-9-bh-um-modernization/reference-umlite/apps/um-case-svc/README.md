# um-case-svc

Spring Boot service that owns the Prior Auth **case**: creates it, persists to Postgres
(schema via Flyway), and exposes it over REST. In Phase 2 it also emits `pa.submitted` and
consumes decisions from Kafka.

## Run
```bash
# from repo root, infra must be up:  docker compose up -d
./mvnw spring-boot:run        # http://localhost:8081
```

## Endpoints
- `POST /api/cases`        create a case
- `GET  /api/cases/{id}`   fetch a case
- `GET  /actuator/health`  health
