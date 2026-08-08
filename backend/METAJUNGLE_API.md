# Meta-Jungle Ecosystem API

Backend for the Meta-Jungle features (Master Prompt v3.0, Chapters 5–13), built
on the existing FastAPI + async SQLAlchemy + Alembic stack. All routes require a
JWT Bearer token.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/reputation/me` | Three reputation scores, role & earn multiplier (Ch. 6) |
| GET | `/api/v1/quests` | Active quest catalog (Ch. 5.2) |
| POST | `/api/v1/quests/{id}/complete` | Complete a quest, award PP (daily cap + role multiplier) |
| GET | `/api/v1/nft` | NFT holdings + total daily PP yield (Ch. 4.7) |
| GET | `/api/v1/p2p/orders?side=buy\|sell` | Open P2P order book (Ch. 4.5) |
| POST | `/api/v1/p2p/orders` | Create order (sellers escrow PP + 50 PP listing fee) |
| GET | `/api/v1/staking` | Active stakes, totals (Ch. 7) |
| POST | `/api/v1/staking` | Lock PP for 30/90/180 days at 1.2×/1.5×/2.0× |
| POST | `/api/v1/staking/{id}/claim` | Claim accrued staking rewards |
| GET | `/api/v1/campaigns` | Active partner campaigns, join-state annotated (Ch. 11) |
| GET | `/api/v1/campaigns/{id}` | One campaign |
| GET | `/api/v1/campaigns/{id}/eligibility` | Targeting check — region, role, min_role |
| POST | `/api/v1/campaigns/{id}/join` | Join a campaign (eligibility enforced) |
| GET | `/api/v1/campaigns/{id}/tasks` | Campaign tasks + the caller's progress today |
| POST | `/api/v1/campaigns/{id}/tasks/{task_id}/complete` | Complete a task, award or reserve PP |
| GET | `/api/v1/learn/courses` | Learn-to-earn courses (Ch. 13) |
| POST | `/api/v1/learn/courses/{id}/quiz` | Submit quiz; 80%+ awards PP once |
| GET | `/api/v1/marketplace/catalog` | VTU + gift-card catalog (Ch. 12) |
| POST | `/api/v1/marketplace/redeem` | Spend PP on a product, returns voucher code |

## PP economy enforcement (Chapter 5)

- **Daily earn cap**: 500 PP (no NFT) / 750 (1 NFT) / 1,200 (3+ NFTs), hard
  ceiling 2,000 PP/day. Enforced on every quest completion.
- **Role multiplier**: quest rewards scale by the caller's role
  (Whitelist 1.2×, OG Panda 1.5×, Alpha OG 2.0×).
- **PP sinks**: marketplace redemptions, staking locks, and the 50 PP P2P
  listing fee deduct from balance via the existing `PointsTransaction` ledger.

Reputation is **derived** from platform activity (streak, quests, level, PP,
account age, email verification, NFT count, referrals, penalties) — no extra
table. Roles follow the Chapter 6.2 thresholds.

## Campaign domain (Chapter 11)

Campaigns live in their own module — `services/campaign_service.py`,
`api/campaigns.py`, `schemas/campaign.py` — so the Chapter-8 `campaign-service`
extraction is a directory move. See `docs/ARCHITECTURE.md`.

**Admin** (all `require_admin`):

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/v1/admin/campaigns` | List every campaign / create one |
| PATCH | `/api/v1/admin/campaigns/{id}` | Set lifecycle status (alias of `/status`) |
| GET/POST | `/api/v1/admin/campaigns/{id}/tasks` | List / create campaign tasks |
| PATCH | `/api/v1/admin/campaigns/{id}/tasks/{task_id}/active` | Enable/disable a task |
| GET | `/api/v1/admin/campaigns/review-queue` | Pending completions awaiting review |
| POST | `/api/v1/admin/campaigns/review-queue/{completion_id}` | Approve or reject |

**Lifecycle**: `draft → active → paused → ended`, enforced by the
`ck_campaign_status` CHECK constraint. Only `active` campaigns inside their date
window are listed, joinable or completable.

**Targeting**: `target_regions` (ISO-3166 alpha-2, matched against `users.region`),
`target_roles` and `min_role` (reputation roles, not auth roles). An empty list
means no restriction on that axis; a populated `target_regions` **excludes** users
with no region set, so partner budget is never spent on an unverifiable audience.

**Billing — reserve → claim → settle**: `oauth`/`webhook` tasks credit the ledger
immediately and add to `pp_claimed`. Every other verification type adds to
`pp_reserved` and waits for review; approval moves the PP to `pp_claimed`,
rejection releases it. A campaign never commits more than `pp_budget` across both,
and task awards are clamped to the remaining budget.

Campaign task rewards go through the same PP economy as quests — role multiplier,
per-task daily limit, and the platform daily earn cap — via
`TransactionType.CAMPAIGN_REWARD`.

## Schema & seed

- Migration: `alembic/versions/010_metajungle_models.py` (11 new tables).
  Run `alembic upgrade head`.
- Campaign architecture: `014_campaign_architecture.py` (campaign tasks,
  completions, targeting columns, `users.region`) and
  `015_add_campaign_reward_enum.py`.
- Seed catalogs (quests, courses, partners, campaigns, campaign tasks):
  `python -m scripts.seed_metajungle` (idempotent).

## Tests

```bash
python -m tests.test_metajungle_integration   # 42 economy + security checks
python -m tests.test_admin_integration        # 18 admin + gate checks
python -m tests.test_campaign_integration     # campaign earn loop, budget, targeting
```

## Notes

- New tables use string-typed status/category columns (validated by Pydantic
  enums) to keep the migration a single atomic step — no Postgres `CREATE TYPE`.
- PP credits/debits reuse the existing `TransactionType.ADMIN_BONUS` /
  `ADMIN_PENALTY` ledger types with descriptive reasons; a dedicated
  `Quest_Reward` / `Redemption` enum value can be added later via migration.
