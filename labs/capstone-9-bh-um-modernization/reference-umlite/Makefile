.PHONY: up down reset ps case intake ui smoke topics case-events case-outbox intake-events watch-decisioned deploy-bpmn case-workflow start-pa

up:      ## start local infra
	docker compose up -d
down:    ## stop infra (keep data)
	docker compose down
reset:   ## wipe + restart infra
	docker compose down -v && docker compose up -d
ps:
	docker compose ps

case:    ## run Spring case service
	cd apps/um-case-svc && ./mvnw spring-boot:run
intake:  ## run NestJS intake service
	cd apps/um-intake-svc && npm install && npm run start
ui:      ## run Angular intake UI
	cd apps/intake-ui && npm install && npm start

smoke:   ## submit a sample prior auth
	curl -s -X POST http://localhost:3000/prior-auth \
	  -H 'content-type: application/json' \
	  -d '{"memberId":"M1001","providerId":"P2002","procedureCode":"27447","diagnosisCode":"M17.11","requestedUnits":1}' | jq .

# ---- Phase 2: event-driven slice (Kafka) ----
topics:  ## create the Prior Auth Kafka topics on Redpanda
	docker exec -i umlite-redpanda rpk topic create pa.submitted pa.decisioned pa.dead-letter --partitions 3 || true
case-events:   ## run the case service in event mode (consumes pa.submitted)
	cd apps/um-case-svc && EVENTS_ENABLED=true ./mvnw spring-boot:run
case-outbox:   ## run the case service in event mode with the transactional outbox (M14)
	cd apps/um-case-svc && EVENTS_ENABLED=true OUTBOX_ENABLED=true ./mvnw spring-boot:run
intake-events: ## run the intake service in event mode (publishes pa.submitted)
	cd apps/um-intake-svc && npm install && EVENTS_ENABLED=true npm run start
watch-decisioned: ## tail pa.decisioned to see auto-decisions
	docker exec -i umlite-redpanda rpk topic consume pa.decisioned --offset start

# ---- Phase 3: workflow & rules (Camunda) ----
deploy-bpmn:   ## deploy the BPMN process + DMN table to Camunda (http://localhost:8088)
	curl -s -w '\n' -F "deployment-name=prior-auth" \
	  -F "prior-auth.bpmn=@camunda/prior-auth.bpmn" \
	  -F "pa-decision.dmn=@camunda/pa-decision.dmn" \
	  http://localhost:8088/engine-rest/deployment/create | jq '.id'
case-workflow: ## run the case service as a Camunda worker (handles the notify-decision task)
	cd apps/um-case-svc && EVENTS_ENABLED=true WORKFLOW_ENABLED=true ./mvnw spring-boot:run
start-pa:      ## start one Prior Auth process instance (caseId, requestedUnits, procedureCode)
	curl -s -w '\n' -H 'content-type: application/json' \
	  -d '{"variables":{"caseId":{"value":"c-demo-1","type":"String"},"requestedUnits":{"value":20,"type":"Integer"},"procedureCode":{"value":"27447","type":"String"}}}' \
	  http://localhost:8088/engine-rest/process-definition/key/prior-auth/start | jq '.id, .ended'
