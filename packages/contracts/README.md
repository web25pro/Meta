# @meta-jungle/contracts

Smart contract layer — **Base L2, Solidity 0.8.24, OpenZeppelin v5, Foundry**
(Master Prompt v3.0, Chapter 7).

> **Status: scaffold only.** Contracts are scheduled for Phase 0–2. This package
> reserves the workspace slot in the monorepo. No Solidity has been written yet.

## Planned contract inventory (Chapter 7.1)

| Contract | Type | Responsibility |
|---|---|---|
| `LPandaPoints.sol` | ERC-20-like (non-standard) | PP ledger, issuance, daily caps, batch settlement, admin controls |
| `LPandaToken.sol` | ERC-20 | LPanda governance & utility token |
| `NFTGate.sol` | Utility | Read NFT holdings, assign tier, verify OG status |
| `PandaWallet.sol` | Escrow + Router | P2P escrow, swap routing, fee collection |
| `StakingVault.sol` | Staking | NFT + token staking, multiplier tiers, lock durations |
| `CampaignRegistry.sol` | Campaign | Campaign deployment, quest proof, reward distribution |
| `UtilityRouter.sol` | Payment | Route PP payments to providers, split platform fee |
| `ReputationOracle.sol` | Oracle | Store/update three-score reputation on-chain |
| `MetaJungleID.sol` | ERC-721 Soulbound | Dynamic ID NFT, non-transferable, score-linked |
| `Treasury.sol` | Finance | Multi-sig treasury, fee accumulation, emission budget |

## Security requirements (Chapter 7.3)

- 100% Foundry test coverage before audit
- Reentrancy guard on every external-call function
- RBAC: `ADMIN`, `ISSUER`, `CAMPAIGN_OPERATOR`, `PAUSER`
- 48h upgrade timelock; UUPS proxy for all non-token contracts
- Two independent audits before mainnet; Immunefi bounty live from day one
