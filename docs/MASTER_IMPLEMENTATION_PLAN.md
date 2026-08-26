# FashionXP — Master Implementation Plan

> Authoritative product spec: `AI Personal Fashion Designer & FashionXP — Final PRD v2.0 (Aug 2026)`
> This document maps every PRD capability to implementation artifacts and defines the build order.
> Companion docs: `IMPLEMENTATION_STATUS.md` (live tracker), `NEXT_STEPS.md` (session handoff).

---

## 1. PRD Requirement Matrix

Legend for "Where": `B`=backend domain app, `M`=mobile, `A`=admin, `J`=background job, `I`=infrastructure, `T`=tests.

| # | PRD Capability | Where | Status |
|---|----------------|-------|--------|
| 8 | Email/password + mobile OTP + Google/Apple auth, sessions, logout-all, reset, deletion | B:`accounts`, M | Phase 0/1 |
| 8 | Onboarding → StyleProfile (styles, colors, fit, budget, occasions) | B:`profiles`, M | Phase 0 |
| 7 | Subscription plans Style / Discover / AI Personal Designer + entitlements | B:`subscriptions` | Phase 0 |
| 9 | AI Personal Stylist: photo → occasion → budget → recommendations | B:`fashion`+`ai`, M | Phase 1 |
| 9 | Occasion engine (wedding…formal/cultural) | B:`fashion` | Phase 1 |
| 9 | Color intelligence (primary/secondary/accent/neutral) | B:`ai` | Phase 1 |
| 10 | Conversational AI designer w/ structured design state + versions | B:`fashion`, M | Phase 1 |
| 11 | Digital wardrobe + AI attribute extraction + combinations | B:`wardrobe`, M | Phase 2 |
| 12 | Daily style assistant (weather-aware, permission-aware) | B:`fashion` | Phase 2 |
| 13–16 | Social network: posts, feeds, follow, like/comment/save/share/report; post creation flow w/ editable AI metadata | B:`social` | Phase 3 |
| 17 | Feed ranking architecture (deterministic scoring first) | B:`social` | Phase 3 |
| 16–20 | FashionXP engine (config rules, ledger, holds, levels, badges) + anti-abuse | B:`fashionxp` | Phase 3 |
| 20 | Challenges + quality-weighted leaderboards | B:`fashionxp` | Phase 3 |
| 19 | Rewards catalog + redemption | B:`fashionxp` | Phase 3 |
| 21 | Creator system (eligibility, portfolio, analytics) | B:`creators` | Phase 6 |
| 22–24 | Designer registration, verification, storefronts, local discovery | B:`designers` | Phase 4 |
| 23 | Brand accounts, storefronts | B:`brands` | Phase 4 |
| 24–26 | Product catalog w/ variants, inventory, customization flags | B:`marketplace` | Phase 4/5 |
| 25 | Semantic fashion search (pgvector + filters) | B:`marketplace` | Phase 4 |
| 22 | Shop This Look (post components → products) | B:`social`+`marketplace` | Phase 4 |
| 27–28 | Customize This Look + quotation lifecycle | B:`marketplace` | Phase 5 |
| 28 | Designer chat w/ moderation | B:`chat` | Phase 5 |
| 30–31 | Order state machine + payment provider abstraction (India-ready), webhooks, idempotency | B:`orders`,`payments` | Phase 5 |
| 29/32 | Brand-creator campaigns, applications, performance | B:`campaigns` | Phase 6 |
| 31 | AI orchestration: providers, routing, fallback, safety, observability | B:`ai` | Phase 1 (core), ongoing |
| 32 | AI cost mgmt: quotas, credits, caching, dup detection, async image gen | B:`ai` | Phase 1 (core) |
| 33–34 | Admin panel: dashboards, user/creator/designer/brand mgmt, XP admin, config | A | Phases 0–5 progressive |
| 35 | Analytics events + aggregation | B:`analytics`, `docs/ANALYTICS_EVENT_TAXONOMY.md` | Phase 1 start |
| 41–43 | Security / privacy / AI-safety controls | cross-cutting | continuous |
| 44 | Performance targets + async processing | cross-cutting | continuous |
| 45 | Accessibility + localization roadmap | M | continuous |

## 2. Architecture

**Modular monolith backend + React Native mobile + web admin later.**

```
Mobile (React Native/Expo)
        │ REST /api/v1
        ▼
Django + DRF (modular monolith)
   ├─ core          base models, middleware, errors, audit, feature flags
   ├─ accounts      users, auth, RBAC, devices
   ├─ profiles      UserProfile, StyleProfile
   ├─ subscriptions plans, entitlements
   ├─ ai            orchestrator, providers, usage, quotas, prompts
   ├─ fashion       occasions, looks, stylist/designer flows
   ├─ wardrobe      items + attributes (Phase 2)
   ├─ social        posts, feed, interactions (Phase 3)
   ├─ fashionxp     XP ledger, badges, challenges (Phase 3)
   ├─ creators / designers / brands / marketplace / orders / payments /
   │  campaigns / chat / notifications / moderation / analytics
        │
        ├── PostgreSQL (+ pgvector) — primary store
        ├── Redis — cache, queues (Celery)
        └── Object storage (S3-compatible; local dev storage adapter)
                │
                ▼
        AI Orchestrator → VisionProvider / LLMProvider / ImageGenProvider / EmbeddingProvider
```

Key decisions:
- **Modular monolith**: one Django project, strict per-domain apps, services layer per domain. No microservices until scale demands.
- **AI provider-agnostic**: all AI calls go through `ai/orchestrator.py`; providers selected via settings; a deterministic `MockAIProvider` powers dev/test so the product runs with zero API keys.
- **Entitlement service**: subscription/AI-quota checks centralized in `subscriptions/services.py`; never scatter plan checks.
- **XP ledger**: every XP change is an immutable `FashionXPTransaction` (planned Phase 3).
- **Config over code**: operational values (quotas, XP values, commission %) live in DB-backed configuration tables, admin-editable, audit-logged.

## 3. Repository Structure

```
fashion/
├── apps/mobile/                 Expo React Native app (TypeScript)
├── apps/admin/                  Web admin (Phase 3+; Django admin until then)
├── backend/
│   ├── config/                  settings/, urls.py, celery.py, asgi, wsgi
│   ├── core/                    shared foundations
│   ├── accounts/  profiles/  subscriptions/
│   ├── ai/  fashion/  wardrobe/
│   ├── social/ fashionxp/ creators/
│   ├── designers/ brands/ marketplace/
│   ├── orders/ payments/ campaigns/ chat/
│   ├── notifications/ moderation/ analytics/
│   ├── manage.py  pytest.ini  requirements/*.txt
├── packages/shared-types/       TS types mirroring API schemas
├── infrastructure/              docker-compose, deploy notes
├── docs/                        living documentation
├── scripts/                     dev helpers
└── .github/workflows/ci.yml
```

## 4. Database Architecture

- UUID PKs (`core.models.TimeStampedUUIDModel`).
- Explicit status enums via TextChoices state machines (orders, quotes).
- Immutable ledgers: FashionXP transactions, payments, audit log (append-only patterns).
- JSONB only where genuinely flexible (AI raw responses, design attributes snapshots).
- Indexes driven by query patterns; migrations in each domain app; seed data via `scripts/seed_demo.py`.

## 5. API Architecture

- Versioned under `/api/v1/`.
- Consistent envelope: `{ "success": true, "data": ... }` / `{ "success": false, "error": {code, message, details} }`.
- Cursor or page pagination; DRF spectacular OpenAPI at `/api/schema/` + Swagger UI.
- Throttling per scope (auth, ai, default); idempotency keys on payment/order endpoints (Phase 5).

## 6. AI Architecture

`AIOrchestrator` facade → router picks provider by task type & config:
- `VisionProvider.analyze_image(image, context)` → validated `ImageAnalysisResult`
- `LLMProvider.complete(messages, schema)` → validated structured JSON
- `ImageGenerationProvider.generate(design)` → async job → storage URL
- `EmbeddingProvider.embed(texts)` (Phase 4 search)

Cross-cutting: prompt templates versioned in code, response validation (Pydantic), safety filter pass, usage row per call (user, feature, provider, model, tokens, latency, cost est., cache hit), quota enforcement before spend, duplicate-request hashing, caching of identical requests.

Providers implemented now: `mock` (deterministic, high-quality demo output), `openai-compatible` (env-configured base URL/key/model). Add more by implementing the protocol.

## 7. Mobile Architecture

Expo + TypeScript. React Navigation bottom tabs: Home(Discover) · Stylist · Create · Wardrobe · Profile.
- `packages` pattern inside `apps/mobile/src`: `theme/` (design tokens), `components/ui/` (Button, Card, Chip, Input, Skeleton, EmptyState, ErrorState…), `api/` (typed client), `navigation/`, `screens/`, `state/` (lightweight stores), `hooks/`.
- Every screen handles Loading / Empty / Error / Success states.
- AI generation states: Queued → Generating → Completed / Failed(Retry).

## 8. Admin Architecture

Phase 0+: hardened Django admin (role-gated) covering users, config, AI usage. Dedicated React admin dashboard arrives when operational volume justifies (tracked as separate phase).

## 9. Security Architecture

JWT (rotation + blacklist), server-side RBAC permission classes, DRF throttling, strict serializer validation, upload MIME/size validation, secrets only via env, audit log for sensitive ops, no PII in logs, CORS allowlist.

## 10. Analytics Architecture

Event taxonomy doc + `analytics.record_event(user, name, props, source)` service writing to `analytics_events`; aggregations via Celery jobs later.

## 11. Testing Strategy

pytest + pytest-django; unit (services), API integration (APIClient), AI orchestrator tests against MockProvider, permission tests, state-machine tests. Critical-flow coverage required before a feature is marked IMPLEMENTED→TESTED.

## 12. Infrastructure Strategy

docker-compose for Postgres+Redis (dev/staging parity). Settings read `DATABASE_URL`, `REDIS_URL`, `AI_PROVIDER`. Local zero-dep mode: SQLite + eager Celery + local media storage + MockAI. GitHub Actions CI: lint (ruff), typecheck (mypy optional), tests. Production deploy doc deferred to DEPLOYMENT.md.

## 13. Implementation Phases

See PRD §48 and execution order §61. Current: **Phase 0 → Phase 1**.

## 14. Dependency Graph

Foundation(auth/profiles/subscriptions/config) → AI orchestrator → fashion(stylist→designer) → media → mobile wow-flow → wardrobe/daily (P2) → social+XP (P3) → designers/brands/products/search (P4) → quotes/orders/payments/chat (P5) → campaigns/creators (P6) → advanced AI (P7).

## 15. Completion Checklist (Definition of Done)

Per feature: UI ✓ API ✓ business logic ✓ persistence ✓ authorization ✓ validation ✓ error handling ✓ analytics ✓ security ✓ tests ✓ docs ✓ — tracked in `IMPLEMENTATION_STATUS.md`.
