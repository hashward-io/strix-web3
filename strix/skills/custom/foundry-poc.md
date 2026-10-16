---
name: foundry-poc
description: Build a minimal Foundry proof-of-concept (fork test) that demonstrates a smart-contract finding end to end
---

# Foundry PoC

A finding without proof is a lead. For every High/Critical, build a minimal Foundry test that demonstrates the impact. This is the standard of proof in Web3 auditing.

## Anatomy

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import {Test} from "forge-std/Test.sol";

contract ExploitTest is Test {
    function setUp() public {
        vm.createSelectFork(vm.envString("ETH_RPC_URL"), FORK_BLOCK);
        // attach to live contracts, deploy mocks, set up the attacker
        attacker = makeAddr("attacker");
        vm.deal(attacker, 100 ether);
    }

    function test_exploit() public {
        uint256 before = token.balanceOf(attacker);

        vm.startPrank(attacker);
        // 1. precondition / manipulation
        // 2. the vulnerable call
        // 3. unwind (repay flash loan)
        vm.stopPrank();

        uint256 after_ = token.balanceOf(attacker);
        assertGt(after_, before, "no profit -> not proven");
    }
}
```

## Rules

1. **Fork when the bug depends on live state** (real token, real oracle, real pool). Pin `--fork-block-number` for determinism; read the RPC URL from an env var.
2. **Minimal.** No unrelated setup. The test should fail before the fix and pass after; revert it (drop the exploit call) to show the opposite.
3. **Assert the impact, not the mechanism.** Assert the profit / the broken invariant / the stuck funds — the property that makes it a finding. Prefer `assertGt`/`assertEq`/`assertTrue` on the concrete consequence.
4. **Use Foundry correctly.** `vm.prank` for one call, `vm.startPrank` for several; `vm.deal` for ETH; `vm.warp`/`vm.roll` for time; `vm.mockCall` for a controlled price; `vm.expectRevert` for a DoS.
5. **Include the loan fee.** For a flash-loan exploit, subtract the fee; the net must be positive.

## When a fork test is not possible

If the target cannot be forked (novel contracts, no deployment), deploy the in-scope contracts locally and reproduce there. If neither is possible, provide a **complete** source→control→sink→impact trace and mark the finding `medium` confidence with an explicit `open_proof_gap` — never claim `confirmed` without proof.

## Verify the fix

After applying a fix, re-run the PoC and confirm it no longer succeeds (`analysis/fix_verification`).
