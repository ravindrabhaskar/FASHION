# FashionXP — AI Personal Fashion Designer

AI-powered personal fashion ecosystem: AI stylist, conversational AI designer, digital wardrobe,
social fashion network, FashionXP rewards, local designers & marketplace.

> Product spec: `docs/MASTER_IMPLEMENTATION_PLAN.md` (maps the Final PRD v2.0 to implementation).

## Repository layout

```
apps/mobile      Expo React Native app (consumer product)
backend          Django + DRF modular monolith (API)
infrastructure   docker-compose for Postgres/Redis
docs             living documentation
scripts          dev helpers
```

## Quickstart — Backend (zero-dependency dev mode)

Requires Python 3.12.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

- API base: `http://127.0.0.1:8000/api/v1/`
- Swagger: `http://127.0.0.1:8000/api/schema/swagger-ui/`
- Django admin: `http://127.0.0.1:8000/admin/` (seeded admin user in `.env.example`)
- Dev mode uses SQLite, Mock AI provider, eager Celery, local file storage — no external services needed.

### With Docker (Postgres + Redis parity)

```powershell
docker compose -f infrastructure/docker-compose.yml up -d
# set DATABASE_URL / REDIS_URL in backend/.env per docker-compose values
```

## Quickstart — Mobile

```powershell
cd apps/mobile
npm.cmd install
npm.cmd start
```

Set API URL in `apps/mobile/.env` (`EXPO_PUBLIC_API_URL=http://<your-lan-ip>:8000/api/v1`).
Scan with Expo Go. Demo account after seeding: `aisha@demo.com` / `demo-pass-123`.

## Testing / linting

```powershell
cd backend
python -m pytest
ruff check .
```

## Documentation index

- docs/MASTER_IMPLEMENTATION_PLAN.md — PRD→implementation map, architecture
- docs/IMPLEMENTATION_STATUS.md — live feature tracker
- docs/NEXT_STEPS.md — session handoff memory
- docs/ANALYTICS_EVENT_TAXONOMY.md — event definitions
