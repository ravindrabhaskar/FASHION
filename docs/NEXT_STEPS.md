# FashionXP — Next Steps (Session Handoff)

Updated: end of session 2.

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

## Architectural decisions to remember
1. **Mock-first AI**: `AI_PROVIDER=mock` default gives deterministic outputs with zero keys; `openai-compatible` activates via `OPENAI_API_KEY`. All AI goes through `backend/ai/orchestrator.py`.
2. **Entitlements centralized** in `subscriptions/services.py::get_entitlements(user)`; scopes include `wardrobe_items`.
3. **Local zero-dependency dev**: SQLite fallback, eager Celery, local media storage, mock AI, seasonal weather fallback — the product runs fully offline.
4. API envelope `{success, data|error}` enforced by core renderer + exception handler.
5. Design state for AI Designer is structured JSONB mutated via explicit ops, versioned per turn.
6. **Wardrobe layering**: pure combination logic lives in `ai/providers/closet.py` (foundation layer) so both the mock provider and the free daily path reuse it without circular imports. Daily GET never spends AI quota; explicit closet styling POST does (`ai_text` scope).

## Partial / known gaps
- Real image generation still stubbed behind vendor choice (`ai/providers/image_gen.py`).
- Google/Apple sign-in + SMS OTP need vendor credentials.
- Wardrobe item images render only when reachable from device (dev uses `http://localhost:8000` absolute URLs in DEBUG — use LAN IP in `.env` for physical devices; S3 backend switches this automatically in prod).
- Daily assistant city comes from profile text field, not device GPS permission (deliberate v1 choice).
- Feed/discovery on mobile Home remains placeholder until Phase 3 social.

## Pending tasks (next recommended order)
1. **Phase 3**: `social` app (posts, feed ranking deterministic-first, follow/like/comment/save/report) + `fashionxp` XP ledger engine (immutable transactions, levels, badges, anti-abuse) per MASTER_IMPLEMENTATION_PLAN §13–20, then mobile Create tab + feed.
2. Wire real vision/LLM keys in `.env` and validate quality vs mock; tune prompts (`ai/prompts.py`, incl. new `wardrobe_system_prompt`).
3. Payment vendor decision before Phase 5 (Razorpay likely) — flag to product owner.

## Exact next action
Start Phase 3: create `backend/social` (Post, Follow, Like/Comment models + feed service with deterministic scoring) and `backend/fashionxp` (config rules + immutable `FashionXPTransaction` ledger), wire XP awards to existing events (outfit_saved, wardrobe_item_added, designer_turn_completed).
