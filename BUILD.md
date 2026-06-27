# Building Meta-Jungle — step by step

How this platform was built, in the order it happened. Doubles as a
reproducible roadmap. Built to the *Meta-Jungle Master Prompt v3.0*.

- **Stack:** Next.js monorepo (`apps/web`, `packages/ui`, `packages/types`) +
  FastAPI backend + PostgreSQL.
- **Brand:** white & cobalt (trust) + jungle green (growth) + bamboo gold
  (rewards only) — "professional jungle with pandas."

---

## Phase 0 — Foundation & design system
1. **Read the spec** and mapped it against the existing repo (FastAPI backend +
   Next.js frontend).
2. **Monorepo** via npm workspaces; moved `frontend/` → `apps/web`; scaffolded
   `apps/mobile` and `packages/contracts`.
3. **`packages/ui`** — the design system: Tailwind preset (color tokens,
   typography Space Grotesk / Inter / JetBrains Mono, spacing, motion) and the
   core component library (StatCard, QuestCard, WalletBalanceCard,
   LeaderboardRow, ReputationRings, PandaMascot, Button, Modal, Badge, …).
4. **`packages/types`** — shared domain model (PP economy, roles, NFTs, quests,
   campaigns).
5. **Rebranded** the landing page and wired the web app onto the tokens.

## Phase 1 — Screens
6. **Restyled every existing screen** (dashboard, auth, community) onto the
   design system. Fixed an auth-context bug that bounced logged-in users to the
   dashboard on hard refresh (now waits for `isLoading`).
7. **Built the feature screens:** Marketplace (VTU + gift cards), NFT Vault,
   P2P Trade, Staking, Campaigns, Learn-to-earn. Added a sectioned sidebar and
   new primitives (Modal, CountUp, Badge, ProgressBar).

## Phase 2 — Backend (the economy)
8. **Meta-Jungle API** on FastAPI: models, schemas, services, routers for
   reputation, quests, NFT vault, P2P, staking, campaigns, learn and
   marketplace. Enforces the PP economy — daily caps (500/750/1,200, hard
   2,000), role multipliers, and PP sinks — through the existing ledger.
9. **Migration + seed** for the 11 new tables and the quest/course/partner/
   campaign catalogs (`alembic upgrade head`, `scripts/seed_metajungle.py`).
10. **Wired the frontend** feature pages to those endpoints, with graceful
    fallback to demo data when the API is unreachable.

## Phase 3 — Testing & hardening
11. **Live end-to-end tests** against real Postgres — 42 integration + security
    assertions, all passing (`tests/test_metajungle_integration.py`).
12. **Fixed two pre-existing ledger bugs** the tests surfaced:
    - `Decimal += float` in `create_transaction` (broke every PP award).
    - enum columns missing `values_callable` (broke inserts and the
      reward-idempotency guard).

## Phase 4 — UI/UX & brand
13. **Elevation pass:** layered shadows, gradient icon chips, richer hero,
    partner strip, fuller footer; `StatCard` scales large numbers so big PP
    totals never overflow.
14. **Brand evolution:** cobalt stays the trust anchor; added jungle green as a
    real secondary plus tasteful SVG `Foliage` and a "jungle-night" gradient.

## Phase 5 — Admin
15. **Admin panel (Overall_Admin only).** Backend `require_admin` gate + CRUD
    for users (roles, ban, PP adjust), quests, partners/campaigns, NFT grants,
    quest-completion review, and an analytics overview. Role-gated `/admin` UI
    (Overview, Users, Quests, Campaigns, Reviews). 18 admin tests passing
    (`tests/test_admin_integration.py`).
16. **Admin creation.** Fixed the broken `scripts/create_admin.py`; added an
    env-driven startup bootstrap (`BOOTSTRAP_ADMIN_*`) so the first admin can be
    minted on deploy without shell/DB access.

## Phase 6 — Security
17. **Untracked `.env`/`.env.production`** from git, tightened `.gitignore`,
    documented host-env config and rotation in `backend/DEPLOY_SECRETS.md`.
18. **Rotated the app signing keys** (`SECRET_KEY`, `JWT_SECRET_KEY`); external
    secrets (Supabase, Resend) must be rotated in their dashboards.

---

## Running it locally

```bash
# Frontend (monorepo root)
npm install
npm run dev            # → http://localhost:3000

# Backend
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:5432/DB
export SECRET_KEY=... JWT_SECRET_KEY=...
alembic upgrade head
python -m scripts.seed_metajungle           # quests/courses/partners/campaigns
uvicorn app.main:app --reload               # → http://localhost:8000

# First admin (either way)
export BOOTSTRAP_ADMIN_EMAIL=you@domain.com BOOTSTRAP_ADMIN_PASSWORD='strong'
# ...starts admin on boot, OR:
python -m scripts.create_admin --email you@domain.com --password 'strong' --username owner
```

## Tests
```bash
cd backend
# against a live Postgres with migrations + seed applied:
python -m tests.test_metajungle_integration   # 42 economy + security checks
python -m tests.test_admin_integration         # 18 admin + gate checks
```

## What's built vs pending
- **Built:** full web UI, the PP/reputation economy backend, admin panel, all
  tested against live Postgres.
- **Pending (per the doc):** Solidity contracts on Base, the React Native app,
  and splitting the monolith into the Chapter-8 microservices.

See also: `docs/ARCHITECTURE.md`, `backend/METAJUNGLE_API.md`,
`backend/DEPLOY_SECRETS.md`.
