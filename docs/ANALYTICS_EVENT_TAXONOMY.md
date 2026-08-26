# FashionXP — Analytics Event Taxonomy

Events are recorded server-side via `analytics.services.record_event(user, name, properties, request, source)`.
Names are lowercase snake_case, immutable once shipped (dashboards depend on them). `source` comes from the
`X-Client` header (`mobile` | `web` | `server`, default `server`); `request_id`/`session_key` captured automatically.

## Auth & onboarding
| Event | When | Key properties |
|---|---|---|
| `onboarding_completed` | StyleProfile saved for first time via onboarding | — |

## Stylist (AI)
| Event | When | Key properties |
|---|---|---|
| `styling_started` | POST /fashion/analyze accepted | `occasion`, `has_notes` |
| `styling_completed` | recommendation persisted | `occasion`, `budget_inr`, `outfit_id`, `confidence` |
| `outfit_generation_queued` | image job queued | `outfit_id`, `task_id` |
| `outfit_generated` | concept outfit/job created (designer materialize or /outfits/generate) | `outfit_id`, `source?` |
| `outfit_saved` | look saved to boards | `outfit_id` |
| `designer_turn_completed` | designer assistant reply stored | `conversation_id`, `changes`, `version` |

## Wardrobe (Phase 2)
| Event | When | Key properties |
|---|---|---|
| `wardrobe_item_added` | item created + attributes extracted | `item_id`, `category` |
| `wardrobe_item_updated` | PATCH name/category/favorite/archive/notes | `item_id` |
| `wardrobe_item_worn` | wear logged | `item_id`, `times_worn` |
| `wardrobe_recommendation_completed` | closet styling persisted | `outfit_id`, `occasion`, `items_used` |
| `daily_suggestion_viewed` | GET /wardrobe/daily served | `occasion`, `has_weather` |

## Conventions
- IDs are stringified UUIDs of the referenced object.
- Counts are ints; booleans are true/false; never include PII (emails/phones) in properties.
- New events must be added to this doc in the same PR that emits them.
