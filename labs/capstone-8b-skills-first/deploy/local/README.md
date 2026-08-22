# Tier 1 -- local

There is nothing to deploy. The compose file in `starter/` (and `solution/`)
IS the Tier 1 deployment:

```bash
cd starter
docker compose up -d oracle postgres
docker compose run --rm agent python coordinator.py --migrate-all
```

Worth saying plainly: this is not only a teaching setup. Restoring a
production Oracle backup into a throwaway container and rehearsing the
whole migration against it -- guardrails, validator, report and all -- is
exactly how you would want to do this for real before touching anything
that matters. The container is disposable; the rehearsal is not.
