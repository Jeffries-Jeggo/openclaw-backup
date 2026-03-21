# FlashFlow - Summary (2026 research)

## Overview
- **DeFi Protocol**: Permissionless leveraged trading (up to 10x) via flash loans.
- **Liquidity**: $10B from Uniswap, 1inch, AAVE, Compound.
- **Chains**: BNB Chain, Polygon, ETH.
- **App**: https://app.flashflow.org (DNS fetch failed; possibly down/migrated).
- **Why?**: Decentralized margin trading without custody.

## Code/Resources
- **Contracts GitHub**: https://github.com/FlashFlow-org/core-contracts
  - Smart contracts for integration.
- **Tor Tool** (unrelated?): https://github.com/pastly/flashflow (Tor relay capacity tester).
- **No SDK/API docs found**; use ethers.js/web3 for contract calls.
- **Example Integration** (pseudocode):
```solidity
// Flash loan + leverage trade (simplified)
interface IFlashFlow {
    function openLeverage(address asset, uint amount, uint leverage) external;
}
```

## Next
Ready for bots, integrations, or UI. Ask confirmation before writes.