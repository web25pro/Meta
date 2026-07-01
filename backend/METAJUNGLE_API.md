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
| GET | `/api/v1/campaigns` | Active partner campaigns (Ch. 11) |
| POST | `/api/v1/campaigns/{id}/join` | Join a campaign |
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

## Schema & seed

- Migration: `alembic/versions/010_metajungle_models.py` (11 new tables).
  Run `alembic upgrade head`.
- Seed catalogs (quests, courses, partners, campaigns):
  `python -m scripts.seed_metajungle` (idempotent).

## Notes

- New tables use string-typed status/category columns (validated by Pydantic
  enums) to keep the migration a single atomic step — no Postgres `CREATE TYPE`.
- PP credits/debits reuse the existing `TransactionType.ADMIN_BONUS` /
  `ADMIN_PENALTY` ledger types with descriptive reasons; a dedicated
  `Quest_Reward` / `Redemption` enum value can be added later via migration.
