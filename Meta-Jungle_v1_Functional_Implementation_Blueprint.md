# Meta-Jungle v1 Functional Implementation Blueprint

**Repository:** `web25pro/Meta`  
**Target stack:** Next.js monorepo + FastAPI + PostgreSQL  
**Purpose:** Convert the current Meta-Jungle implementation from a mixture of working UI, partial backend logic, legacy modules, and simulated Web3/economic behavior into a coherent, secure, production-ready v1.

> This document is intentionally implementation-focused. It is meant to be handed directly to the developer working in the existing repository.

---

# 1. Executive Goal

Do **not** rewrite the entire project.

Do **not** split the backend into microservices yet.

Do **not** market or display on-chain behavior that does not exist yet.

The correct approach is to keep the current monorepo and FastAPI backend, then restructure it into a **modular monolith** with one canonical identity system, one canonical Panda Points economy, one verification engine, and clear feature state machines.

The required dependency order is:

```text
Identity
   ↓
PP Ledger / Balances
   ↓
Reputation
   ↓
Verification Engine
   ↓
Earn Features
   ├── Quests
   ├── Campaigns
   ├── Learn-to-Earn
   └── Referrals
   ↓
Spend / Financial Features
   ├── Marketplace
   ├── P2P
   └── Staking
   ↓
NFT / Wallet Integration
   ↓
Community
   ├── Leaderboard
   ├── Schedule
   ├── Announcements
   └── Notifications
   ↓
Admin / Moderation / Audit
```

Every feature must use this chain instead of maintaining isolated balances, counters, verification rules, or user logic.

---

# 2. Current Repository Areas That Must Be Reconciled

The repository currently contains logic from multiple product generations:

```text
Legacy internal platform
├── Team_Member
├── Ambassador
├── internal tasks
├── schedule
├── announcements
└── team/ambassador leaderboard

Public community system
├── Community_User
├── registration
├── verification
├── referrals
└── public task submission

Meta-Jungle economy system
├── Panda Points
├── reputation roles
├── quests
├── campaigns
├── NFT vault
├── P2P
├── staking
├── learn-to-earn
└── marketplace
```

These must become one system.

The most important rule for the refactor is:

> **Authorization roles and gamification/reputation roles are different concepts and must never be mixed.**

---

# 3. Canonical User Model

## 3.1 Authentication Roles

Replace the product-facing use of the current mixed roles with a simple authorization layer:

```text
USER
MODERATOR
ADMIN
SUPER_ADMIN
```

The existing legacy values can remain temporarily for migration compatibility, but new feature authorization should use the new canonical role model.

Recommended enum:

```python
class AccountRole(str, Enum):
    USER = "User"
    MODERATOR = "Moderator"
    ADMIN = "Admin"
    SUPER_ADMIN = "Super_Admin"
```

If retaining `UserRole` initially, map:

```text
Community_User → User
User           → User
Team_Member    → User
Ambassador     → User
Ambassador_Admin → Moderator/Admin depending on current permission requirements
Overall_Admin    → Super_Admin
```

Do not destroy existing data in the first migration.

Add a canonical `account_role` column first, migrate values, then gradually remove runtime reliance on `role`.

---

## 3.2 Reputation Roles

Reputation roles remain separate:

```text
Explorer
Tracker
Hunter
Whitelist
OG Panda
Alpha OG
```

These roles control:

- earn multiplier
- quest eligibility
- campaign eligibility
- NFT/community gating
- leaderboard display
- feature unlocks

They must **not** control admin permissions.

---

# 4. Phase 0: Disable False or Unsafe Behavior First

Before deeper backend refactoring, remove or disable UI that currently claims successful behavior without actually performing it.

This phase should be shipped first.

---

## 4.1 Files to Change Immediately

### `apps/web/src/app/(dashboard)/dashboard/tasks/page.tsx`

Remove:

```ts
proof.verified = true
```

for `oauth` and `webhook`.

Do not allow the browser to self-verify a quest.

Temporary behavior:

```text
oauth/webhook quest
→ POST attempt
→ backend creates VERIFYING record
→ UI displays "Verification in progress"
```

Until provider verification exists, disable these quest types or mark them `manual`.

---

### `apps/web/src/app/(dashboard)/dashboard/campaigns/page.tsx`

Remove:

```ts
return { verified: true };
```

for OAuth/webhook campaign tasks.

Use the same verification engine as normal quests.

---

### `apps/web/src/app/(dashboard)/dashboard/community/settings/page.tsx`

Current behavior falsely reports password change and account deletion success.

Replace the handlers with real API calls.

Until APIs exist:

- Disable Change Password button.
- Disable Delete Account button.
- Show `Coming soon` or remove the controls.

Never show success for an operation that never happened.

---

### `apps/web/src/app/(dashboard)/dashboard/p2p/page.tsx`

Remove or replace these claims until implemented:

```text
"on-chain escrow"
"PP is locked in smart-contract escrow"
"1.5% trade fee"
```

The smart contracts are not currently implemented.

Temporary wording:

```text
"P2P trading is being prepared. Escrow trading is not yet enabled."
```

Disable the trade button until Phase 5.

---

### `apps/web/src/app/(dashboard)/dashboard/staking/page.tsx`

Do not display APR values unless they are backed by a real accrual formula.

Current hardcoded:

```text
30d  8%
90d 14%
180d 22%
```

Either:

1. remove APR completely and treat staking only as an earning multiplier, or
2. implement the exact reward-rate model in Phase 5 before enabling new stakes.

For immediate safety, disable new staking if existing principal-return behavior is incomplete.

---

### `apps/web/src/app/(dashboard)/dashboard/marketplace/page.tsx`

Disable actual redemption until provider fulfillment exists.

Do not report:

```text
Redemption complete
Your voucher/reference
```

from a locally generated `MJ-*` code.

Temporary state:

```text
Marketplace Preview
Redemptions are not yet live.
```

---

### `apps/web/src/app/(dashboard)/dashboard/nft-vault/page.tsx`

Keep NFT Vault read-only.

Remove/disable:

```text
List for Sale
Transfer
```

until wallet ownership and contract support exist.

---

# 5. Phase 1: Rebuild the Panda Points Economic Core

This is the highest-priority backend change.

Current PP logic must become atomic, auditable and concurrency-safe.

---

# 6. Database Changes: Economy

Create a new migration after the current Alembic head.

Suggested migration name:

```text
016_economy_ledger_hardening.py
```

If the actual Alembic head has moved, renumber accordingly.

---

## 6.1 Add Balance Buckets

Add to `users` temporarily:

```text
available_points NUMERIC(18,2)
locked_points    NUMERIC(18,2)
escrow_points    NUMERIC(18,2)
```

Migration initialization:

```text
available_points = existing users.points
locked_points = 0
escrow_points = 0
```

Keep `points` temporarily for backward compatibility.

Eventually either:

- make `points` a generated/cached total, or
- deprecate it completely.

Recommended derived total:

```text
total_points = available_points + locked_points + escrow_points
```

---

## 6.2 Replace Generic Point Transactions With a Canonical Ledger

Current file:

```text
backend/app/models/points_and_audit.py
```

Expand the transaction model or create:

```text
pp_ledger_entries
```

Recommended fields:

```text
id UUID PK
user_id UUID
amount NUMERIC(18,2)
bucket VARCHAR
transaction_type VARCHAR
source_type VARCHAR
source_id UUID / VARCHAR
idempotency_key VARCHAR UNIQUE NULLABLE
status VARCHAR
metadata JSONB
created_at TIMESTAMPTZ
```

Recommended buckets:

```text
available
locked
escrow
campaign_reserved
redemption_clearing
treasury
```

Recommended transaction types:

```text
QUEST_REWARD
CAMPAIGN_REWARD
LEARNING_REWARD
REFERRAL_REWARD
ADMIN_ADJUSTMENT

P2P_ESCROW_LOCK
P2P_ESCROW_RELEASE
P2P_ESCROW_REFUND
P2P_LISTING_FEE
P2P_TRADE_FEE

STAKE_LOCK
STAKE_UNLOCK
STAKE_REWARD
STAKE_EARLY_EXIT_PENALTY

MARKETPLACE_RESERVE
MARKETPLACE_SETTLE
MARKETPLACE_REFUND

TRANSFER_SENT
TRANSFER_RECEIVED

NFT_REWARD

MIGRATION_OPENING_BALANCE
```

Stop using `ADMIN_BONUS` and `ADMIN_PENALTY` as generic stand-ins for unrelated economic operations.

---

# 7. Critical Change: Remove Internal Commits From Services

Current issue is centered in:

```text
backend/app/services/points_service.py
```

`PointsService.create_transaction()` currently commits.

Change this.

Service layer functions must:

```python
db.add(...)
await db.flush()
```

but **must not** call:

```python
await db.commit()
```

The request-level database dependency already has request-scoped commit/rollback behavior.

Correct rule:

```text
One business operation
= one database transaction
= one commit
```

Examples:

```text
Marketplace redemption reserve + redemption record
must commit together.

Stake balance move + stake record
must commit together.

P2P escrow lock + order creation
must commit together.

Campaign budget reserve + completion record
must commit together.
```

---

# 8. Concurrency Safety

For every economic operation that checks and changes balances, use row locking.

Example:

```python
user = (
    await db.execute(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
    )
).scalar_one()
```

Then validate balance and mutate it within that same transaction.

Apply locking to:

```text
user balances
campaign budgets
P2P orders
stakes when claiming/unlocking
redemptions
referral reward state
```

For campaign participant limits:

```text
lock campaign row
check current participants
insert participation
increment counter
```

Do not rely on unlocked counters.

---

# 9. Idempotency

Current middleware:

```text
backend/app/middleware/idempotency.py
```

uses process memory and a five-minute TTL.

Replace it with persistent idempotency.

Create table:

```text
idempotency_keys
```

Fields:

```text
key
user_id
method
path
body_hash
status_code
response_json
created_at
expires_at
```

Unique:

```text
(user_id, key)
```

For economic endpoints, enforce idempotency keys in PostgreSQL or Redis.

Recommended endpoints requiring idempotency:

```text
POST quest attempts
POST campaign completions
POST transfers
POST P2P orders
POST P2P accept/payment/release
POST stakes
POST unstake
POST marketplace redeem
POST referral payouts
POST admin point adjustment
```

---

# 10. Phase 2: Identity and Session Cleanup

Suggested migration:

```text
017_identity_referrals_sessions.py
```

---

# 11. One Authentication Guard

Current central dependency:

```text
backend/app/api/user.py
get_current_user()
```

Extend it.

Canonical authenticated guard:

```python
async def get_current_user(...):
    # token valid
    # user exists
    # not deleted
    # active
    # session still valid
```

Add separate guard:

```python
async def get_economic_user(...):
    user = await get_current_user(...)
    if not user.email_verified:
        raise 403 EMAIL_NOT_VERIFIED
    if not user.is_active:
        raise 403 ACCOUNT_SUSPENDED
    return user
```

Use `get_economic_user` for:

```text
quests complete
campaign join/complete
learn rewards
referrals reward
marketplace
P2P
staking
PP transfer
NFT rewards
```

Browsing may remain available to authenticated-but-unverified accounts where appropriate.

---

# 12. Login Unification

Current relevant files:

```text
backend/app/api/auth.py
backend/app/api/community.py
apps/web/src/app/auth/login/page.tsx
apps/web/src/api/community.ts
```

Choose **one** login route:

```text
POST /api/v1/auth/login
```

Return:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "...",
    "email": "...",
    "username": "...",
    "email_verified": true,
    "account_role": "User"
  }
}
```

Deprecate:

```text
POST /community/login
```

after the web frontend migrates.

---

# 13. Registration

Canonical:

```text
POST /api/v1/auth/register
```

Input:

```json
{
  "email": "...",
  "username": "...",
  "password": "...",
  "referral_code": "optional"
}
```

State:

```text
REGISTERED
→ EMAIL_PENDING
→ ACTIVE
```

Do not award any economic reward before email verification.

---

# 14. Password Reset

Current JWT-only reset logic should become one-time-use.

Create table:

```text
password_reset_tokens
```

Fields:

```text
id
user_id
token_hash
expires_at
used_at
created_at
```

Flow:

```text
request reset
→ generate random token
→ store hash
→ email raw token
→ confirm reset
→ hash submitted token
→ lookup valid unused token
→ update password
→ mark used
→ revoke all sessions
```

---

# 15. Change Password Endpoint

Add:

```text
POST /api/v1/auth/change-password
```

Input:

```json
{
  "current_password": "...",
  "new_password": "..."
}
```

Requirements:

```text
verify current password
validate complexity
change password
set password_changed_at
revoke refresh sessions
return success
```

Wire:

```text
apps/web/src/app/(dashboard)/dashboard/community/settings/page.tsx
```

---

# 16. Account Deletion

Add:

```text
DELETE /api/v1/users/me
```

Prefer soft deletion first.

Behavior:

```text
set deleted_at
set is_active = false
revoke sessions
anonymize personal fields if product/legal policy requires it
retain immutable economic audit records
```

The frontend must only show success after a 2xx response.

---

# 17. Referral Data Model

Create table:

```text
referrals
```

Fields:

```text
id
referrer_id
referred_user_id UNIQUE
referral_code
status
registered_at
verified_at
qualification_started_at
qualified_at
rewarded_at
reward_pp
risk_status
risk_metadata JSONB
created_at
updated_at
```

Statuses:

```text
REGISTERED
VERIFIED
QUALIFYING
QUALIFIED
REWARDED
FLAGGED
REJECTED
```

Do not rely on `users.referred_by_id` as the only business record.

Retain it temporarily for compatibility.

---

# 18. Referral Policy Must Be Server-Side

Create configuration, e.g.:

```text
referral_policy
```

or application config:

```text
reward_pp = 300
required_approved_quests = 3
qualification_window_days = 7
```

Frontend should request:

```text
GET /api/v1/referrals/me
```

Response:

```json
{
  "referral_code": "...",
  "referral_link": "...",
  "total_referrals": 10,
  "qualified_referrals": 4,
  "rewarded_referrals": 3,
  "referral_earnings": 900,
  "policy": {
    "reward_pp": 300,
    "required_approved_quests": 3,
    "qualification_window_days": 7
  }
}
```

Replace the current missing `/community/referral-stats` flow.

---

# 19. Fix Existing Referral Route Bug

Current:

```text
backend/app/api/community.py
```

uses `settings.SITE_BASE_URL` in referral-code behavior.

Ensure:

```python
from app.core.config import settings
```

exists if this route remains during migration.

Also generate the correct current frontend URL:

```text
/auth/register?ref=CODE
```

not:

```text
/register?ref=CODE
```

---

# 20. Phase 3: Verification Engine

Suggested migration:

```text
018_verification_engine.py
```

Create new module:

```text
backend/app/verification/
```

Recommended structure:

```text
verification/
├── models.py
├── schemas.py
├── service.py
├── providers/
│   ├── base.py
│   ├── manual.py
│   ├── oauth.py
│   ├── webhook.py
│   └── onchain.py
└── api.py
```

---

# 21. Verification Record

Create:

```text
verification_attempts
```

Fields:

```text
id
user_id
source_type
source_id
verification_type
status
submitted_proof JSONB
provider_reference
provider_response JSONB
reviewed_by_id
reviewed_at
failure_reason
created_at
updated_at
```

Statuses:

```text
STARTED
SUBMITTED
VERIFYING
VERIFIED
REJECTED
FAILED
EXPIRED
```

---

# 22. Verification Rules

## OAuth

Browser initiates OAuth.

Server stores linked provider account.

Quest completion asks server:

```text
Did this linked provider account perform the required action?
```

The browser never sends `verified=true`.

---

## Webhook

Provider sends signed webhook.

Backend verifies signature.

Backend stores event.

Quest engine matches event to:

```text
user
quest
required action
time window
```

---

## On-chain

Input may include:

```text
tx_hash
wallet_address
```

Server verifies through Base RPC/indexer:

```text
transaction exists
successful receipt
correct chain
correct contract
correct sender
required event/action occurred
not previously consumed for another reward
```

Create uniqueness on consumed tx/event IDs.

---

## Screenshot

Do not accept only a string URL.

Add file upload support.

Store:

```text
file key
mime type
hash
size
uploaded_at
```

Admin review displays the actual evidence.

---

## Manual

Store a text note and optional evidence.

Admin decides.

---

# 23. Quest Model Refactor

Suggested fields:

```text
id
title
description
category
base_pp
starts_at
ends_at
daily_limit
total_limit
minimum_reputation_role
verification_type
verification_config JSONB
action_url
steps JSONB
is_active
reward_budget NULLABLE
created_at
updated_at
deleted_at
```

---

# 24. Quest Attempt State Machine

Use:

```text
AVAILABLE
→ STARTED
→ SUBMITTED
→ VERIFYING
→ APPROVED
→ REWARDED
```

Failure paths:

```text
SUBMITTED → REJECTED
VERIFYING → FAILED
```

Create table:

```text
quest_attempts
```

or evolve `QuestCompletion`.

Fields:

```text
id
user_id
quest_id
status
verification_attempt_id
base_pp
multiplier
final_pp
reward_transaction_id
created_at
verified_at
rewarded_at
```

Never reward directly from a client-submitted boolean.

---

# 25. Quest Reward Logic

Pseudo-code:

```python
async with transaction:
    user = lock_user()

    assert economic_user(user)

    quest = lock/read quest

    assert active
    assert started
    assert not expired
    assert role eligible
    assert daily quest limit

    attempt = create_attempt()

    verification = run_or_queue_verification()

    if verification != VERIFIED:
        return pending

    reputation = calculate_reputation(user)

    raw_reward = quest.base_pp * reputation.multiplier

    daily_remaining = get_daily_earn_remaining(user)

    quest_budget_remaining = get_quest_budget_remaining(quest)

    final_reward = min(
        raw_reward,
        daily_remaining,
        quest_budget_remaining
    )

    ledger.credit_available(
        user,
        QUEST_REWARD,
        final_reward,
        source_id=attempt.id
    )

    attempt.status = REWARDED
```

---

# 26. Daily Earn Cap Definition

Do not calculate today's earnings by simply summing every positive transaction.

Only include earn types:

```text
QUEST_REWARD
CAMPAIGN_REWARD
LEARNING_REWARD
REFERRAL_REWARD
NFT_REWARD
```

Do **not** count:

```text
P2P receipt
PP transfer received
stake principal return
marketplace refund
admin correction
escrow release
```

Implement:

```python
EARN_TRANSACTION_TYPES = {...}
```

and filter by that list.

---

# 27. Reputation Service Refactor

Current location:

```text
backend/app/services/metajungle_service.py
```

Extract reputation logic into:

```text
backend/app/economy/reputation_service.py
```

Keep the three scores:

```text
activity_score
reputation_score
influence_score
```

Add:

```text
formula_version
calculated_at
```

Optional cache table:

```text
user_reputation_cache
```

The canonical role is derived from the scores.

Do not store a manually editable reputation role unless explicitly required.

---

# 28. Phase 3B: Campaigns

The current campaign module is comparatively strong.

Keep:

```text
backend/app/services/campaign_service.py
backend/app/api/campaigns.py
backend/app/schemas/campaign.py
```

but integrate it with the new economy and verification modules.

---

# 29. Campaign State Machine

Use:

```text
DRAFT
→ FUNDED
→ SCHEDULED
→ ACTIVE
→ PAUSED
→ ENDED
```

Current simpler lifecycle can be migrated gradually.

A campaign cannot become `ACTIVE` unless its budget is funded.

---

# 30. Campaign Budget Ledger

Create campaign accounts or explicit balance fields:

```text
budget_total
budget_available
budget_reserved
budget_claimed
```

Prefer deriving them from a campaign ledger if practical.

On manual task submission:

```text
budget_available → budget_reserved
```

On approval:

```text
budget_reserved → user available PP
```

On rejection:

```text
budget_reserved → budget_available
```

On auto-verified completion:

```text
budget_available → user available PP
```

All in one DB transaction.

Lock the campaign row during reserve/settlement.

---

# 31. Campaign Verification

Delete campaign-specific proof logic that trusts:

```text
{"verified": true}
```

Campaign tasks must call the same shared verification service used by normal quests.

---

# 32. Phase 4: Learn-to-Earn

Suggested migration:

```text
019_learning_progress.py
```

Create:

```text
courses
course_modules
lessons
lesson_completions
course_progress
quiz_attempts
course_completions
```

Current `courses` can be evolved rather than recreated if possible.

---

# 33. Course API

Canonical endpoints:

```text
GET  /api/v1/learn/courses
GET  /api/v1/learn/courses/{course_id}
GET  /api/v1/learn/courses/{course_id}/progress

POST /api/v1/learn/lessons/{lesson_id}/complete

GET  /api/v1/learn/courses/{course_id}/quiz
POST /api/v1/learn/courses/{course_id}/quiz-attempts
```

---

# 34. Fix Current Quiz Contract

Current frontend expects quiz content, but current backend response does not expose the expected structure.

Return safe quiz payload:

```json
{
  "id": "...",
  "questions": [
    {
      "id": "...",
      "question": "...",
      "options": ["...", "..."]
    }
  ]
}
```

Never return:

```text
correct option index
answer key
grading rule that reveals answers
```

Backend grades by question ID.

---

# 35. Course Progress

Remove frontend hardcoding:

```ts
progress: 0
```

Backend returns:

```json
{
  "completed_lessons": 3,
  "total_lessons": 5,
  "progress_percent": 60,
  "quiz_unlocked": false,
  "course_completed": false
}
```

---

# 36. Learning Reward

Reward once per course version.

Create unique constraint:

```text
(user_id, course_id, course_version)
```

Reward only after:

```text
all required lessons completed
AND quiz score >= pass threshold
AND no previous rewarded completion for this version
```

---

# 37. Phase 4B: Public Leaderboard

The current legacy leaderboard only ranks Team Members and Ambassadors.

Create a public Meta-Jungle leaderboard.

Suggested migration:

```text
020_public_leaderboard.py
```

Recommended tabs/data:

```text
Season PP
Reputation
Influence
Referrals
```

---

# 38. Seasonal Leaderboard

Create:

```text
seasons
```

Fields:

```text
id
name
starts_at
ends_at
status
```

Leaderboard score should use qualifying earned PP only.

Do not rank users by transferred/refunded/stake-returned points.

Use:

```text
EARN_TRANSACTION_TYPES
```

---

# 39. New Leaderboard Endpoints

```text
GET /api/v1/leaderboard/season
GET /api/v1/leaderboard/reputation
GET /api/v1/leaderboard/influence
GET /api/v1/leaderboard/referrals
GET /api/v1/leaderboard/me
```

Deprecate public use of:

```text
/team-members
/ambassadors
```

Those may remain as admin/internal reporting routes.

---

# 40. Phase 5: Panda Wallet

Current frontend:

```text
apps/web/src/app/(dashboard)/dashboard/points/page.tsx
```

must stop reconstructing balance from paginated transactions.

Use:

```text
GET /api/v1/wallet
```

Response:

```json
{
  "available_pp": 4200,
  "locked_pp": 1000,
  "escrow_pp": 500,
  "total_pp": 5700,
  "earned_today": 250,
  "daily_earn_cap": 750,
  "daily_earn_remaining": 500
}
```

History:

```text
GET /api/v1/wallet/transactions
```

---

# 41. Fix Pagination Globally

The frontend shared type currently assumes:

```ts
items: T[]
```

while multiple backend endpoints return domain-specific names.

Standardize every paginated endpoint to:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

Apply to:

```text
points transactions
schedule
announcements
leaderboard
submissions
referrals
admin review queues
P2P
redemptions
```

---

# 42. Generate Frontend Types From OpenAPI

Current frontend type duplication should be removed over time.

Recommended:

```text
FastAPI OpenAPI
→ generated TypeScript types
→ apps/web uses generated contracts
```

Options:

```text
openapi-typescript
orval
openapi-generator
```

Create package:

```text
packages/api-types
```

Generated from:

```text
/openapi.json
```

Do not manually maintain response field names in multiple locations.

---

# 43. Wallet Internal Transfers

Add only after ledger hardening.

Endpoint:

```text
POST /api/v1/wallet/transfers
```

Input:

```json
{
  "recipient": "username-or-user-id",
  "amount": 500
}
```

Transaction:

```text
sender available -500
recipient available +500
```

Use one transfer group/reference ID.

Require:

```text
verified sender
verified recipient
sufficient available balance
idempotency key
rate limits
fraud controls
```

Optional PIN/2FA can come later.

---

# 44. Wallet Buttons

Frontend behavior:

```text
Send     → transfer modal
Receive  → username/QR/share page
Stake    → /dashboard/staking
Swap     → hidden until real implementation
```

Never render a dead action.

---

# 45. Phase 6: P2P

Suggested migration:

```text
021_p2p_escrow_and_trades.py
```

Existing `P2POrder` can be evolved.

Add:

```text
p2p_trades
p2p_trade_events
p2p_disputes
p2p_evidence
```

---

# 46. P2P Order States

```text
OPEN
PARTIALLY_FILLED
FILLED
CANCELLED
EXPIRED
```

For v1, simplify to full-order matching only:

```text
OPEN
RESERVED
FILLED
CANCELLED
EXPIRED
```

---

# 47. P2P Trade States

```text
RESERVED
AWAITING_PAYMENT
PAYMENT_MARKED
RELEASED
CANCELLED
EXPIRED
DISPUTED
REFUNDED
```

---

# 48. Correct Sell Order Logic

Current behavior checks seller balance but does not lock the amount being sold.

Correct:

```python
required = pp_amount + listing_fee

lock seller

if seller.available_pp < required:
    reject

move pp_amount:
available → escrow

charge listing fee:
available → treasury

create order
```

Order stores:

```text
escrowed_pp = pp_amount
```

Canceling an unmatched order:

```text
escrow → available
```

Listing fee policy must be explicit.

If the fee is supposed to be refunded on completion, create:

```text
P2P_LISTING_FEE
P2P_LISTING_FEE_REFUND
```

If not refundable, remove that frontend statement.

---

# 49. P2P Buyer Flow

```text
POST /p2p/orders/{id}/accept
```

Transaction:

```text
lock order
ensure OPEN
ensure buyer != seller
create trade
order.status = RESERVED
```

Response includes payment instructions.

Do not expose full bank information publicly in order-book listing.

---

# 50. Buyer Marks Payment

```text
POST /p2p/trades/{id}/payment-marked
```

Optional evidence upload.

State:

```text
AWAITING_PAYMENT → PAYMENT_MARKED
```

---

# 51. Seller Releases

```text
POST /p2p/trades/{id}/release
```

Transaction:

```text
lock trade
lock seller/buyer
ensure PAYMENT_MARKED
seller escrow -pp
buyer available +pp
fees settle
trade RELEASED
order FILLED
```

---

# 52. P2P Dispute

```text
POST /p2p/trades/{id}/dispute
```

Admin routes:

```text
GET  /api/v1/admin/p2p/disputes
POST /api/v1/admin/p2p/disputes/{id}/release
POST /api/v1/admin/p2p/disputes/{id}/refund
```

Admin must see:

```text
trade details
seller/buyer history
timestamps
payment evidence
messages/notes
reputation
previous disputes
```

---

# 53. Phase 7: Staking

Suggested migration:

```text
022_staking_lifecycle.py
```

Current stake model needs:

```text
principal_pp
started_at
matures_at
reward_rate
multiplier
rewards_claimed
status
unstaked_at
early_exit_penalty
```

Statuses:

```text
ACTIVE
MATURED
UNSTAKED
EARLY_EXIT
CANCELLED
```

---

# 54. Decide What Staking Means

The product currently mixes:

```text
earn multiplier
and
APR yield
```

Choose one of these explicitly.

## Recommended v1

Use staking primarily for **earn multiplier**, and either:

- no PP APR initially, or
- a clearly configured small PP yield.

If APR remains, create a backend config table.

Do not hardcode APR only in React.

---

# 55. Staking Balance Movement

Create stake:

```text
available → locked
```

Never simply deduct principal from the user.

At maturity:

```text
locked → available
```

Reward:

```text
treasury/reward pool → available
```

Early exit:

```text
locked principal
→ penalty account + returned available principal
```

---

# 56. Accrual Formula

If rewards are enabled:

```text
accrued
=
principal
× annual_rate
× elapsed_seconds
/ seconds_per_year
```

Then:

```text
claimable = accrued - already_claimed
```

Never rely on a stale manually updated `accrued` value without a defined accrual job or formula.

---

# 57. Claim Endpoint

```text
POST /api/v1/staking/{id}/claim-rewards
```

Only rewards.

Do not return principal.

---

# 58. Unstake Endpoint

```text
POST /api/v1/staking/{id}/unstake
```

Behavior:

```text
if matured:
    return full locked principal
else:
    calculate penalty
    require confirmation token/parameter
    return principal minus penalty
```

Frontend should display exact amounts before confirming.

---

# 59. Phase 8: Marketplace

Suggested migration:

```text
023_marketplace_fulfillment.py
```

Current random voucher generation must be replaced.

Create:

```text
marketplace_products
provider_quotes
redemptions
redemption_events
```

---

# 60. Redemption States

```text
CREATED
PP_RESERVED
PROCESSING
FULFILLED
FAILED
REFUNDING
REFUNDED
```

---

# 61. Provider Adapter Interface

Create:

```text
backend/app/commerce/providers/base.py
```

Interface:

```python
class UtilityProvider:
    async def validate_destination(...)
    async def get_quote(...)
    async def purchase(...)
    async def get_status(...)
```

Then adapters:

```text
providers/
├── airtime_provider.py
├── data_provider.py
├── electricity_provider.py
├── cable_provider.py
└── giftcard_provider.py
```

The exact external providers can be selected separately.

Do not bake provider-specific behavior into `MetaJungleService`.

---

# 62. Marketplace Purchase Flow

```text
1. User selects product.
2. Backend fetches/validates current product price.
3. User confirms.
4. Lock user.
5. available PP → redemption clearing.
6. Create redemption.
7. Commit.
8. Worker/provider call starts.
9. On provider success:
       clearing → settled/treasury
       redemption FULFILLED
10. On failure:
       clearing → user available
       redemption REFUNDED
```

External API calls should preferably run outside the same database transaction using an outbox/job pattern.

---

# 63. Provider Reference

Successful response must contain actual provider data:

```text
provider_transaction_id
provider_reference
voucher_code if applicable
delivered_at
```

Do not generate a fake `MJ-*` voucher as the purchased utility.

You may still create an internal Meta-Jungle order ID such as:

```text
MJ-RDM-XXXX
```

but label it clearly as the **Meta-Jungle order reference**, not the provider voucher.

---

# 64. Phase 9: Wallet Connection and NFT Vault

Suggested migration:

```text
024_linked_wallets_and_nft_sync.py
```

Create:

```text
linked_wallets
wallet_nonces
nft_collections
nft_holdings
nft_sync_runs
```

---

# 65. Wallet Connection

Endpoint:

```text
POST /api/v1/wallets/nonce
```

Response:

```text
nonce + message
```

User signs message.

Then:

```text
POST /api/v1/wallets/verify
```

Server:

```text
recovers signer
checks nonce
marks nonce used
links wallet
```

Do not accept an arbitrary wallet address as proof of ownership.

---

# 66. NFT Sync

For approved Base collections:

```text
query RPC/indexer
verify token ownership
store contract_address
token_id
metadata
tier
last_verified_at
```

Holdings are a cache of verified on-chain ownership, not manually invented records.

---

# 67. Admin NFT Grants

Current `admin-grant` database holdings should be renamed if they remain.

If the product needs off-chain entitlements, call them:

```text
NFT entitlement
badge
access pass
```

Do not call them NFTs unless actual token ownership exists.

---

# 68. NFT Daily PP Yield

If NFTs generate daily PP:

Create a scheduled reward job.

For each eligible verified NFT holding:

```text
last_rewarded_date
daily_rate
collection rules
```

Use unique constraint:

```text
(user_id, contract_address, token_id, reward_date)
```

to prevent duplicate rewards.

---

# 69. NFT Transfer / Sale

Do not implement until contracts/wallet transaction support exists.

The contract package is currently scaffold-only.

Keep these features hidden until:

```text
contracts implemented
Foundry tests complete
testnet deployment
security review
frontend wallet transaction flow
```

---

# 70. Phase 10: Community Update System

Suggested migration:

```text
025_audience_notifications.py
```

Legacy targeting:

```text
Team_Members
Ambassadors
All
```

should be replaced for public Meta-Jungle features.

---

# 71. Audience Model

Create reusable audience definition:

```text
EVERYONE
REGION
REPUTATION_ROLE
CAMPAIGN_PARTICIPANTS
NFT_HOLDERS
SPECIFIC_USERS
```

An announcement/schedule record should contain:

```text
audience_type
audience_config JSONB
```

Examples:

```json
{
  "audience_type": "REGION",
  "audience_config": {"regions": ["NG", "GH"]}
}
```

```json
{
  "audience_type": "REPUTATION_ROLE",
  "audience_config": {"roles": ["OG Panda", "Alpha OG"]}
}
```

---

# 72. Schedule API

Canonical:

```text
GET /api/v1/schedule
```

Response uses `items`.

Do not treat `Community_User` as Ambassador by default.

Audience resolution must be explicit.

---

# 73. Announcement API

Canonical:

```text
GET /api/v1/announcements
```

Response:

```json
{
  "items": [...],
  "total": ...,
  "page": ...,
  "page_size": ...,
  "total_pages": ...
}
```

Frontend should not guess field names.

---

# 74. Notifications

Create:

```text
notifications
```

Fields:

```text
id
user_id
type
title
body
action_url
read_at
metadata JSONB
created_at
```

Create notifications for:

```text
quest approved
quest rejected
campaign task approved/rejected
referral qualified
referral rewarded
P2P order matched
buyer marked payment
trade released
trade dispute update
stake matured
staking reward claimed
marketplace fulfilled
marketplace refunded
admin security action
```

---

# 75. Outbox Pattern

For emails, webhooks, provider fulfillment, push notifications and blockchain sync, create:

```text
outbox_events
```

Fields:

```text
id
event_type
aggregate_type
aggregate_id
payload JSONB
status
attempt_count
next_attempt_at
created_at
processed_at
```

Business transaction writes both:

```text
domain change
+
outbox event
```

in one DB transaction.

Worker processes outbox later.

This prevents:

```text
DB says success
but email/provider/webhook never happened
```

without any retry record.

---

# 76. Phase 11: Admin Panel Completion

Current admin UI should evolve from CRUD-only into an operations console.

---

# 77. Admin Modules

Required sections:

```text
Overview
Users
Quests
Quest Review
Campaigns
Campaign Review
Referrals / Fraud
P2P Disputes
Marketplace Reconciliation
Staking
NFT Sync
Announcements
Schedules
Audit Logs
System Health
```

---

# 78. Quest Review Evidence

Current admin completion listing must return submitted proof.

Add fields:

```text
proof
verification_type
verification_status
verification_attempt_id
evidence_files
provider_response_summary
risk_flags
```

Admin UI must display the evidence before approving.

---

# 79. Admin Review State

Review records:

```text
reviewed_by
reviewed_at
decision
reason
```

Require rejection reason.

Recommended endpoint:

```text
POST /api/v1/admin/quest-attempts/{id}/review
```

Input:

```json
{
  "decision": "approve",
  "reason": "..."
}
```

or:

```json
{
  "decision": "reject",
  "reason": "Screenshot does not show required action."
}
```

---

# 80. Audit Logging

Audit all privileged actions:

```text
user suspension
role change
manual PP adjustment
quest creation/update/delete
manual review decision
campaign status/funding change
P2P dispute decision
marketplace manual refund
NFT override
staking configuration
announcement/schedule creation
```

Audit fields:

```text
admin_user_id
action
resource_type
resource_id
before JSONB
after JSONB
reason
ip
user_agent
created_at
```

---

# 81. Proposed Backend Module Layout

Refactor incrementally toward:

```text
backend/app/

  identity/
      models.py
      schemas.py
      service.py
      auth_service.py
      referral_service.py
      wallet_link_service.py
      api.py

  economy/
      ledger_models.py
      ledger_service.py
      balance_service.py
      cap_service.py
      reputation_service.py

  verification/
      models.py
      schemas.py
      service.py
      providers/
          manual.py
          oauth.py
          webhook.py
          onchain.py

  quests/
      models.py
      schemas.py
      service.py
      api.py

  campaigns/
      models.py
      schemas.py
      service.py
      api.py

  learning/
      models.py
      schemas.py
      service.py
      api.py

  commerce/
      marketplace_models.py
      redemption_service.py
      providers/
      api.py

  trading/
      models.py
      order_service.py
      trade_service.py
      dispute_service.py
      api.py

  staking/
      models.py
      service.py
      api.py

  nft/
      models.py
      sync_service.py
      api.py

  community/
      leaderboard_service.py
      audience_service.py
      notification_service.py
      api.py

  admin/
      service.py
      api.py

  infrastructure/
      database.py
      idempotency.py
      outbox.py
      workers.py
```

Do not physically move every file in one commit.

First establish service boundaries, then move files once tests cover them.

---

# 82. API Versioning

Keep existing:

```text
/api/v1
```

Do not create `/v2` just for cleanup unless breaking compatibility cannot be avoided.

For endpoints with major behavior changes:

1. add new canonical endpoint,
2. migrate frontend,
3. mark old endpoint deprecated,
4. remove old endpoint only after no consumers remain.

---

# 83. Canonical API Response Rules

## Success object

For single resources:

```json
{
  "id": "...",
  "...": "..."
}
```

No unnecessary wrapper required.

---

## Paginated resource

Always:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

---

## Error

Standardize:

```json
{
  "error": {
    "code": "INSUFFICIENT_PP",
    "message": "You do not have enough available Panda Points.",
    "details": {
      "required": 1000,
      "available": 750
    }
  }
}
```

Do not mix:

```text
detail: string
error.message
plain strings
```

across features.

Add a central FastAPI exception handler.

---

# 84. Exact Existing Frontend Files to Audit/Modify

Primary user application:

```text
apps/web/src/lib/api.ts
apps/web/src/api/community.ts
apps/web/src/api/metajungle.ts
apps/web/src/types/index.ts
apps/web/src/context/auth-context.tsx

apps/web/src/app/auth/register/page.tsx
apps/web/src/app/auth/login/page.tsx
apps/web/src/app/auth/password-reset/page.tsx
apps/web/src/app/auth/password-reset-confirm/page.tsx
apps/web/src/app/auth/resend-verification/page.tsx

apps/web/src/app/(dashboard)/layout.tsx
apps/web/src/app/(dashboard)/dashboard/page.tsx
apps/web/src/app/(dashboard)/dashboard/tasks/page.tsx
apps/web/src/app/(dashboard)/dashboard/campaigns/page.tsx
apps/web/src/app/(dashboard)/dashboard/learn/page.tsx
apps/web/src/app/(dashboard)/dashboard/points/page.tsx
apps/web/src/app/(dashboard)/dashboard/marketplace/page.tsx
apps/web/src/app/(dashboard)/dashboard/p2p/page.tsx
apps/web/src/app/(dashboard)/dashboard/staking/page.tsx
apps/web/src/app/(dashboard)/dashboard/nft-vault/page.tsx
apps/web/src/app/(dashboard)/dashboard/leaderboard/page.tsx
apps/web/src/app/(dashboard)/dashboard/community/profile/page.tsx
apps/web/src/app/(dashboard)/dashboard/community/referrals/page.tsx
apps/web/src/app/(dashboard)/dashboard/community/settings/page.tsx
apps/web/src/app/(dashboard)/dashboard/schedule/page.tsx
apps/web/src/app/(dashboard)/dashboard/announcements/page.tsx
```

---

# 85. Exact Existing Backend Files to Audit/Modify

Core:

```text
backend/app/core/database.py
backend/app/core/security.py
backend/app/core/config.py
backend/app/core/email.py

backend/app/middleware/idempotency.py
backend/app/main.py
```

Identity:

```text
backend/app/models/user.py
backend/app/services/user_service.py
backend/app/services/community_service.py
backend/app/api/auth.py
backend/app/api/community.py
backend/app/api/user.py
backend/app/schemas/auth.py
backend/app/schemas/community.py
backend/app/schemas/user.py
```

Economy:

```text
backend/app/models/points_and_audit.py
backend/app/services/points_service.py
backend/app/api/points.py
backend/app/schemas/points.py

backend/app/services/metajungle_service.py
backend/app/api/metajungle.py
backend/app/models/metajungle.py
backend/app/schemas/metajungle.py
```

Campaigns:

```text
backend/app/services/campaign_service.py
backend/app/api/campaigns.py
backend/app/schemas/campaign.py
```

Community:

```text
backend/app/services/leaderboard_service.py
backend/app/api/leaderboard.py
backend/app/api/schedule.py
backend/app/schemas/schedule.py
backend/app/api/announcement.py
backend/app/schemas/announcement.py
```

Admin:

```text
backend/app/api/admin.py
backend/app/services/admin_service.py
backend/app/schemas/admin.py
```

---

# 86. Frontend Profile Fix

Current profile page expects fields not returned by `/users/me/stats`.

Replace this with a canonical endpoint:

```text
GET /api/v1/profile/me
```

Response:

```json
{
  "id": "...",
  "username": "...",
  "email": "...",
  "email_verified": true,
  "account_role": "User",
  "available_pp": 5000,
  "xp": 1200,
  "level": 2,
  "current_streak": 4,
  "best_streak": 12,
  "approved_quests": 35,
  "referrals_count": 7,
  "created_at": "...",
  "reputation": {
    "activity_score": 400,
    "reputation_score": 310,
    "influence_score": 120,
    "role": "Hunter"
  }
}
```

One request should populate the profile.

---

# 87. Dashboard Aggregate Endpoint

Instead of many fragile frontend calls, create:

```text
GET /api/v1/dashboard
```

Response:

```json
{
  "user": {...},
  "wallet": {...},
  "reputation": {...},
  "season_rank": 18,
  "quest_stats": {...},
  "active_quests": [...],
  "notifications_unread": 3
}
```

This reduces request count and schema drift.

---

# 88. Environment Configuration

Add explicit configuration for each optional integration.

Example:

```text
SITE_BASE_URL
API_BASE_URL

DATABASE_URL
REDIS_URL

RESEND_API_KEY
EMAIL_FROM

BASE_RPC_URL
BASE_CHAIN_ID

MARKETPLACE_PROVIDER
MARKETPLACE_PROVIDER_API_KEY

OAUTH_X_CLIENT_ID
OAUTH_X_CLIENT_SECRET

WEBHOOK_SIGNING_SECRET

S3_BUCKET
S3_REGION
S3_ACCESS_KEY
S3_SECRET_KEY

REFERRAL_REWARD_PP
REFERRAL_REQUIRED_QUESTS
REFERRAL_WINDOW_DAYS
```

No code should silently behave as if an integration succeeded when its configuration is absent.

---

# 89. Smart Contracts: Correct Scope

Current contract workspace should remain separate until the off-chain v1 is stable.

Planned package:

```text
packages/contracts
```

Do not claim contracts are live until they actually contain deployed/tested Solidity.

Recommended later implementation order:

```text
1. NFTGate
2. StakingVault
3. PandaWallet escrow/router
4. UtilityRouter
5. CampaignRegistry
6. ReputationOracle
7. MetaJungleID
8. Treasury
9. any PP/token contract
```

Before production:

```text
Foundry tests
testnet deployment
invariant tests
access-control tests
reentrancy tests
upgrade tests
external security review
mainnet deployment
```

---

# 90. Test Strategy

Existing tests are valuable but are currently too shallow for several features.

Keep them, then add state-machine and concurrency coverage.

---

# 91. Economy Tests

Create:

```text
backend/tests/test_ledger_atomicity.py
backend/tests/test_ledger_concurrency.py
backend/tests/test_idempotency_persistence.py
```

Must test:

```text
double spend prevented
same idempotency key does not duplicate debit
two simultaneous spends cannot make balance negative
failed record creation rolls back balance mutation
refund restores correct bucket
ledger sum matches cached balances
```

---

# 92. Quest Tests

Create:

```text
test_quest_verification.py
```

Must test:

```text
browser cannot self-verify oauth
browser cannot self-verify webhook
same on-chain tx cannot reward twice
manual proof stays pending
admin sees proof
approval rewards once
second approval does not duplicate PP
rejection does not reward
daily cap counts only earning types
```

---

# 93. Campaign Tests

Extend:

```text
backend/tests/test_campaign_integration.py
```

Add:

```text
concurrent completions cannot overspend budget
participant limit is concurrency safe
pending completion reserves budget
rejection releases reserve
approval settles exactly once
provider verification required
```

---

# 94. Referral Tests

Must test:

```text
self-referral blocked
invalid code blocked
verification moves state
3 approved quests qualifies according to policy
qualification outside time window fails
reward paid once
duplicate worker run does not duplicate reward
```

---

# 95. Learning Tests

Must test:

```text
quiz response never leaks answers
lessons update progress
quiz locked until requirements met
pass threshold enforced
reward only once per course version
```

---

# 96. P2P Tests

Must test:

```text
sell order moves PP to escrow
same PP cannot be listed twice
cancel restores escrow
buyer cannot accept own order
only reserved buyer can mark payment
only seller/admin can release
release transfers escrow once
duplicate release safe
dispute freezes trade
admin release/refund settles correctly
```

---

# 97. Staking Tests

Must test:

```text
stake moves available → locked
principal never disappears
maturity calculation correct
claim only pays rewards
unstake returns principal
early exit applies exact penalty
duplicate claim/unstake prevented
```

---

# 98. Marketplace Tests

Use a fake provider adapter.

Test:

```text
reserve PP
provider success
settlement
provider failure
automatic refund
provider timeout
retry
duplicate webhook/provider callback
idempotent redemption
```

Do not treat a random local code as fulfillment.

---

# 99. NFT Tests

Use mocked Base RPC/indexer.

Test:

```text
nonce can only be used once
wrong signer rejected
wallet ownership verified
NFT ownership sync updates holdings
removed NFT no longer grants benefits
same token cannot duplicate reward
```

---

# 100. End-to-End Tests

Add Playwright tests for the user app.

Critical journeys:

```text
register
verify email
login
complete manual quest
admin approve quest
wallet balance updates

complete course
earn PP

referral registration
qualification
reward

P2P sell
buyer accept
payment marked
seller release

stake
maturity simulation
unstake

marketplace success
marketplace failure/refund
```

---

# 101. Recommended Commit Sequence

Do not put this restructure in one enormous pull request.

Use this sequence.

---

## Commit 1 — Truthful UI

```text
Disable fake marketplace redemption
Disable fake smart-contract P2P copy/actions
Disable incomplete staking action
Remove client self-verification
Disable fake account settings success
Hide unsupported NFT actions
```

No database changes.

---

## Commit 2 — API Contract Fixes

```text
Standard pagination
Fix wallet transaction response mismatch
Use /points/balance
Fix profile stat mismatch
Fix schedule response mismatch
Fix announcement response mismatch
Fix referral endpoint/import/path bug
```

---

## Commit 3 — Atomic PP Ledger

```text
Migration 016
Balance buckets
Ledger transaction types
No internal service commits
Row locking
Ledger tests
```

---

## Commit 4 — Persistent Idempotency

```text
idempotency_keys table
DB/Redis middleware/service
economic endpoints adopt it
```

---

## Commit 5 — Identity Cleanup

```text
canonical login
economic-user guard
active/suspended enforcement
change password
delete account
session revocation
```

---

## Commit 6 — Referral Domain

```text
referrals table
policy
stats endpoint
qualification worker/event logic
fraud flags
```

---

## Commit 7 — Verification Engine

```text
verification_attempts
manual verification
on-chain verification interface
oauth/webhook provider interfaces
quest integration
admin proof display
```

---

## Commit 8 — Quest Refactor

```text
attempt state machine
reward settlement
daily earning cap fix
budget support
```

---

## Commit 9 — Campaign Integration

```text
shared verification
shared ledger
locking
funding state
```

---

## Commit 10 — Learn-to-Earn

```text
lessons
progress
safe quiz API
course completion
reward once
```

---

## Commit 11 — Public Leaderboard

```text
community users included
season leaderboard
reputation/influence/referral tabs
```

---

## Commit 12 — Wallet v1

```text
canonical wallet endpoint
send/receive
history
bucket balances
```

---

## Commit 13 — P2P v1

```text
real escrow buckets
trades
payment states
release
cancel
dispute
admin dispute UI
```

---

## Commit 14 — Staking v1

```text
locked principal
maturity
accrual
claim
unstake
early exit
```

---

## Commit 15 — Marketplace Provider Layer

```text
provider adapters
clearing balance
outbox/worker
success
failure
refund
reconciliation
```

---

## Commit 16 — Wallet Signature + NFT Sync

```text
wallet nonce/signature
Base RPC/indexer
verified holdings
read-only vault
NFT-gated benefits
```

---

## Commit 17 — Community Audiences + Notifications

```text
audience model
schedule
announcements
notifications
```

---

## Commit 18 — Contract Preparation

```text
only after off-chain system stable
start Foundry contracts
testnet first
```

---

# 102. Definition of Done by Feature

A feature is **not done** because:

```text
screen exists
button exists
endpoint returns 200
database row is created
happy-path unit test passes
```

A feature is done only when its full state transition is implemented and tested.

---

## Quest Done

```text
User performs action
→ server verifies action
→ duplicate/fraud controls pass
→ reward calculation occurs
→ PP ledger settles atomically
→ UI updates
→ admin can audit result
```

---

## Marketplace Done

```text
User confirms purchase
→ PP reserved
→ provider fulfills
→ success settles OR failure refunds
→ provider reference stored
→ user receives correct status
→ reconciliation possible
```

---

## P2P Done

```text
Seller PP locked
→ buyer accepts
→ payment tracked
→ release/refund/dispute supported
→ escrow settles exactly once
→ balances remain correct
```

---

## Staking Done

```text
Principal moves to locked balance
→ maturity/reward formula works
→ reward claim works
→ principal returns
→ early exit works if enabled
```

---

## NFT Done

```text
User proves wallet ownership
→ server verifies chain holdings
→ holdings update
→ utility rules use verified holdings
```

---

# 103. Immediate Bug-Fix Checklist

These can be addressed before the full architecture work:

```text
[ ] Import settings in backend/app/api/community.py
[ ] Fix referral link to /auth/register
[ ] Replace /community/referral-stats missing call
[ ] Change wallet frontend from data.items to canonical response
[ ] Use /points/balance for displayed wallet balance
[ ] Fix profile stats response names
[ ] Fix schedule items/schedules mismatch
[ ] Fix announcements items/announcements mismatch
[ ] Add Community_User to public leaderboard or replace leaderboard entirely
[ ] Add is_active check to auth guard
[ ] Add email_verified check to economic guard
[ ] Remove client proof.verified = true
[ ] Include proof in admin review response
[ ] Disable fake password-change success
[ ] Disable fake delete-account success
[ ] Disable fake marketplace completion
[ ] Disable unsupported NFT transfer/listing
[ ] Remove smart-contract escrow claim from P2P UI
[ ] Stop PointsService.create_transaction from committing
[ ] Add row locking for economic writes
[ ] Replace in-memory idempotency
```

---

# 104. Recommended Product Scope for Meta-Jungle v1

To ship a stable v1 sooner, define **v1** as:

```text
Authentication
Email verification
Profile
PP wallet
Quests
Manual + internal verification
Campaigns
Learn-to-Earn
Referrals
Reputation
Leaderboard
Announcements
Schedule
Admin moderation
Off-chain P2P escrow
Off-chain PP staking
Real provider-backed marketplace
Read-only Base NFT verification
```

Defer:

```text
on-chain PP tokenization
fully on-chain P2P
NFT transfer marketplace
NFT staking contracts
governance token
MetaJungle soulbound identity NFT
microservices split
React Native app
```

This avoids another cycle where the product looks bigger than the infrastructure underneath it.

---

# 105. Final Architecture Principle

The repository should enforce four universal rules:

## Rule 1

**The frontend never decides that a rewardable action is verified.**

---

## Rule 2

**Every Panda Point movement must pass through the canonical ledger.**

---

## Rule 3

**Every multi-step economic operation must be atomic and idempotent.**

---

## Rule 4

**The UI must never report a completed financial/security/Web3 action until the backend has actually completed it.**

---

# 106. Recommended First Pull Request Scope

The first developer PR should be intentionally narrow:

```text
Title:
fix(core): remove fake feature completion and align API contracts
```

Include only:

```text
1. Remove quest/campaign self-verification.
2. Fix referral settings import and URL.
3. Fix wallet response shape and balance source.
4. Fix profile stats contract.
5. Fix schedule/announcement pagination shape.
6. Disable fake password/account deletion.
7. Disable fake marketplace redemption.
8. Disable incomplete P2P/staking/NFT transactional actions.
9. Add regression tests for each contract mismatch.
```

Then immediately start the ledger PR.

---

# 107. Recommended Second Pull Request Scope

```text
Title:
refactor(economy): introduce atomic Panda Points ledger
```

Include:

```text
1. Migration for available/locked/escrow PP.
2. Dedicated ledger transaction types.
3. Remove commits from PointsService.
4. Add row locking.
5. Add persistent idempotency.
6. Update quest/campaign rewards to new ledger.
7. Add concurrency and rollback tests.
```

No P2P or Marketplace feature expansion should happen until this PR is complete.

---

# 108. Recommended Third Pull Request Scope

```text
Title:
refactor(identity): unify public account and economic authorization
```

Include:

```text
1. Canonical login.
2. Economic-user guard.
3. Suspended account enforcement.
4. Verified-email enforcement.
5. Password change API.
6. Account deletion API.
7. Refresh/session revocation.
8. Referral domain migration.
```

---

# 109. Handoff Summary for Developer

The current codebase should be treated as a strong **prototype with several real backend components**, not as a production-complete economy.

Do not throw away:

```text
Next.js design system
FastAPI structure
SQLAlchemy/Alembic
campaign domain
reputation concept
admin foundation
existing quest/course/catalog UI
existing tests
```

Do replace or redesign:

```text
client-controlled verification
generic PP mutation
service-level commits
in-memory idempotency
fake fulfillment
fake escrow
incomplete staking lifecycle
legacy leaderboard assumptions
legacy audience assumptions
manual frontend/backend type duplication
```

The sequence is:

```text
make UI truthful
→ fix API contracts
→ secure PP ledger
→ unify identity
→ verification engine
→ earn features
→ wallet
→ P2P/staking
→ marketplace
→ NFT verification
→ contracts later
```

That sequence produces a real, testable Meta-Jungle platform without requiring a full rewrite.
