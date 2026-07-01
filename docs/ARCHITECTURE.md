# Meta-Jungle — Target Architecture & Migration Plan

This document tracks how the repository moves from its current shape toward the
architecture defined in the **Master Development Prompt v3.0**.

## Decision: migrate toward the document's architecture

The document specifies a Node.js + Solidity + React Native stack across nine
microservices (Chapter 8). The repository started as a working **FastAPI +
Next.js** task-and-reward app. The agreed direction is to **migrate toward the
document's architecture incrementally**, beginning with Phase 0, rather than a
single big-bang rewrite — so the platform keeps working at every step.

## Phase 0 — Foundation (done in this pass)

The document's own kickoff is _"set up the monorepo and implement the design
system tokens from Chapter 3."_ That is what this pass delivers:

- **Monorepo** via npm workspaces: `apps/*`, `packages/*`.
- **`packages/ui`** — the canonical White & Blue "Panda in the Jungle" design
  system: Tailwind preset (all Chapter 3.2 color tokens, 3.3 typography, 3.4
  spacing, 3.7 motion), CSS token file, and the Chapter 3.6 component library
  (StatCard, QuestCard, LeaderboardRow, WalletBalanceCard, P2POrderCard,
  NFTVaultTile, NotificationToast, ReputationRings, PandaMascot, Button, …).
- **`packages/types`** — shared domain model from Chapters 5, 6 and 9 (PP
  economy constants, role thresholds, ledger, quests, NFTs, P2P, campaigns).
- **`apps/web`** — the existing Next.js app, moved into the monorepo, rebranded
  onto the new tokens (Space Grotesk / Inter / JetBrains Mono), with the
  landing page rebuilt to Chapter 4.1. Legacy dashboard/auth pages keep working
  via a recolored compatibility palette and will be restyled screen-by-screen
  in later passes.
- **Scaffolds** for `packages/contracts` (Chapter 7) and `apps/mobile`
  (Phase 4), reserving their workspace slots.

## Service map (Chapter 8 — target)

Redis is intentionally excluded everywhere; caching/queues/leaderboards run on
PostgreSQL (materialized views + pg_cron) and BullMQ via pg-boss.

| Service | Responsibility |
|---|---|
| auth-service | SIWE, JWT, OAuth, sessions |
| identity-service | Profile, NFT verification, tiers, reputation |
| quest-service | Quest defs, verification, webhooks |
| ledger-service | PP issuance, balance, anti-fraud |
| wallet-service | P2P escrow, swap, fiat ramps |
| campaign-service | Partner campaigns, targeting, billing |
| utility-service | Airtime, tickets, gift cards, DeFi |
| notification-service | Push, email, in-app |
| analytics-service | Events, dashboards, leaderboard compute |

## Migration sequence (next passes)

1. **Design system adoption** — restyle dashboard + auth screens onto
   `@meta-jungle/ui` (Quests, Panda Wallet, Leaderboard, Profile w/ rings).
2. **Backend alignment** — extend the current API toward the PP economy and
   three-score reputation model (Chapters 5–6); introduce the ledger and role
   thresholds. Then begin extracting the Chapter 8 service boundaries.
3. **Contracts** — implement and test the Chapter 7 contracts on Base Sepolia.
4. **Wallet & P2P, Utility & Partners, Mobile, Governance** — Phases 2–5.

## Current backend

`backend/` remains a FastAPI service (auth, tasks, submissions, points,
leaderboard, community, announcements). It is the live API today and the
starting point for the Chapter 8 migration; it is not deleted.
