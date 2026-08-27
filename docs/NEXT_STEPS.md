# FashionXP — Next Steps (Session Handoff)

Updated: end of session 2c (Phase 7 delivered).

## Completed
- **Session 1**: Phase 0 foundation (core, accounts w/ JWT+RBAC, profiles, subscriptions/entitlements, analytics recorder, docker-compose, CI) + full Phase 1 (AI orchestrator w/ mock & openai-compatible providers, usage/cost ledger, quotas, caching, duplicate detection; fashion domain: occasion engine, color intelligence, photo analysis, recommendations, async outfit image jobs, conversational designer with versioned design state, saved looks, media validation) + mobile wow-flows.
- **Session 2 — Phase 2 complete**:
  - `backend/wardrobe` app: `WardrobeItem` model (categories, AI-extracted attributes snapshot, favorite/archive/wear tracking), photo → attribute extraction via `orchestrator.extract_wardrobe_attributes` (tracked as its own `wardrobe_extract` feature so it never eats stylist quota), CRUD/filter/wear endpoints under `/api/v1/wardrobe/*`, entitlement `wardrobe_item_limit` enforced.
  - Closet combination engine (`ai/providers/closet.py`, pure + deterministic): scores items by formality/occasion/favorite, prefers one-piece looks on formal occasions, reports gaps ("add footwear…"), returns `used_item_ids`. Mock provider delegates to it; real LLM providers get a wardrobe prompt (`ai.prompts.wardrobe_system_prompt`) and must echo ids.
  - POST `/wardrobe/closet/recommend`: quota'd AI styling from user's own clothes → persists `GeneratedOutfit(source=WARDROBE)` with used ids in `design_state.wardrobe_item_ids`; saveable through the existing saved-looks flow. Requires ≥2 READY items (`wardrobe_too_small` otherwise).
  - GET `/wardrobe/daily`: daily style assistant — weather-aware via keyless Open-Meteo (30-min cache; deterministic seasonal fallback when offline), occasion chosen from style profile + weekday/weekend, free deterministic closet pick (no AI spend on GET). City from query param or UserProfile.city.
  - Weather module `wardrobe/weather.py`; `RecommendationResult.used_item_ids` added (additive schema change); `GeneratedOutfit.Source.WARDROBE` added.
  - Mobile: Wardrobe tab fully built (item grid w/ filters, add via camera/gallery with analyzing state, favorite/wear/delete actions, "Today's pick" card with weather + closet mini-pick, "Style from my closet ✦" flow with save-to-looks). Home cards now navigate to Stylist/Designer/Wardrobe. Fixed all pre-existing `tsc --noEmit` errors and added typed navigation (`src/navigation/types.ts`). Mobile CI typecheck is green.
  - Backend: 48 pytest tests green, ruff clean. Seed command adds demo wardrobes for aisha (6 pieces) and rohit (5 pieces).
- **Session 2 (cont.) — Phases 3–6 mobile complete** (backend for these phases was already fully implemented/tested):
  - 16 new/updated screens wired to real APIs: Social feed/detail/create (with AI caption suggestions, report, shop-the-look), Public profile, XP dashboard/leaderboard/challenges/rewards, Notifications (+ device-token registration on sign-in), Marketplace products + search, Product detail (buy now → order → payment, request custom quote, chat, variant select), My products + create/edit/delete with photo upload, Designers (+become designer), Brands (+become brand, storefront grid), Creators (+become creator, eligibility), Campaigns (+create campaign, apply, review applications), Quotes (request/list/detail, accept offer → order), Orders (state-machine transitions matching backend statuses), Payment (mock gateway initiate/confirm), Report.
  - Backend additions this session: `POST /marketplace/products/:id/buy` + `OrderService.create_from_catalog` (catalog purchase → order); `order_payload` now includes `seller_name`/`customer_name`; `product_payload` exposes `sale_price_inr`, `colors`, `in_stock`, `image`, `seller_user_id`.
  - Mobile types aligned to actual backend payloads (Product, ProductVariant, Order, DesignerProfile, CreatorProfile/CreatorEligibility, SearchResult). All 40 screens registered in the navigator; `tsc --noEmit` green; `manage.py check` green.
- **Session 2c — Phase 7 (Advanced AI) complete**:
  - Backend: `fashion/i18n.py` translation catalog (9 locales: en hi bn ta te mr gu kn ur, English fallback); `fashion/trends.py` deterministic `trend_snapshot` (colors/fabrics/categories/hashtags/cities — hashtags parsed from post captions, no AI spend); `GET /fashion/trends`, `GET /fashion/i18n/strings?lang=`, `POST /ai/translate` (quota'd, mode `dict`→`pass-through`→`llm`), `POST /fashion/outfits/:id/tryon` (mock image generator, flag enabled by default). Fixed `TryOnView` URL-kwarg bug + `refresh_from_db` for eager jobs; `transcribe` now logs `TRANSCRIBE` feature; AIUsageLog.Feature gained TRANSCRIBE/TRANSLATE/TRYON (no migration). Marketplace `ProductDetailView.patch` now accepts multipart `photo` (replaces/creates ProductImage) and no longer references a bogus `payload`; `order_payload` `name` → `full_name` fix.
  - Backend tests: `fashion/tests/test_phase7.py` (6 tests) + `marketplace/tests/test_purchase.py` (buy + PATCH photo). Suite: 60 green, `manage.py check` clean.
  - Mobile: deps `expo-av`, `expo-notifications`, `expo-constants`, `expo-auth-session`, `expo-web-browser`. New screens `Trends`, `TryOn`, `Language` registered in the navigator; `I18nProvider` (fetch + persist + patch profile, offline English fallback); Login gains SMS OTP (dev_code surfaced) + Google/Apple buttons; CreatePost gets a mic (expo-av record → `/ai/transcribe`); CreateProduct edit path now uploads replaced photos; push registration tries a real Expo push token then falls back to the stable per-install id. Home + Profile got Phase 7 entries. `tsc --noEmit` clean.

## Architectural decisions to remember
1. **Mock-first AI**: `AI_PROVIDER=mock` default gives deterministic outputs with zero keys; `openai-compatible` activates via `OPENAI_API_KEY`. All AI goes through `backend/ai/orchestrator.py`.
2. **Entitlements centralized** in `subscriptions/services.py::get_entitlements(user)`; scopes include `wardrobe_items`.
3. **Local zero-dependency dev**: SQLite fallback, eager Celery, local media storage, mock AI, seasonal weather fallback — the product runs fully offline.
4. API envelope `{success, data|error}` enforced by core renderer + exception handler.
5. Design state for AI Designer is structured JSONB mutated via explicit ops, versioned per turn.
6. **Wardrobe layering**: pure combination logic lives in `ai/providers/closet.py` (foundation layer) so both the mock provider and the free daily path reuse it without circular imports. Daily GET never spends AI quota; explicit closet styling POST does (`ai_text` scope).

## Partial / known gaps
- Real image generation still stubbed behind vendor choice (`ai/providers/image_gen.py`); try-on articulates the final leg but uses the same mock. Fun pic pass-through is next.
- Google/Apple sign-in + SMS OTP need vendor credentials (client ids in `.env`/`GOOGLE_OAUTH_CLIENT_IDS`; buttons surface a clear warning until configured; OTP works in DEBUG via `dev_code`).
- Voice caption transcription quality is tied to the active AI provider (mock = deterministic).
- Wardrobe/item images render only when reachable from device (dev uses `http://localhost:8000` absolute URLs in DEBUG — use LAN IP in `.env` for physical devices; S3 backend switches this automatically in prod).
- Daily assistant city comes from profile text field, not device GPS permission (deliberate v1 choice).
- Push: `expo-notifications` native token is used when a dev build with the push config exists; otherwise we keep the stable per-install id (Emulator/Expo Go path).
- Marketplace photo upload works for create AND edit now; no multi-photo gallery or primary-image ordering UI yet.

## Pending tasks (next recommended order)
1. Mobile component/render smoke tests (Expo Router-less RN testing setup) — screens currently verified via `tsc` only.
2. Wire real vision/LLM keys in `.env` and validate quality vs mock; tune prompts (`backend/ai/prompts.py`).
3. Payment vendor decision before production (Razorpay likely) — flag to product owner; replace mock-gateway confirm with webhook-driven flow.
4. Ops: SMS/OTP provider (e.g. MSG91/Twilio) + Apple/Google OAuth client ids, then real push EXPO_ACCESS_TOKEN for `eas push` broadcasts.

## Exact next action
Add an RN test harness + first smoke tests for the Phase 7 screens (Trends/TryOn/Language) and the post/buy flows, then finish UX polish across screens (empty states, skeletons, pull-to-refresh parity).
