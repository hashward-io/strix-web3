---
name: foundry
description: Foundry toolkit — forge build/test/fuzz/invariant, fork tests, scripting, and the project layout for Solidity audits
---

# Foundry

Foundry is the primary toolchain. Master `forge`, `cast`, and `anvil`.

## Project layout and build

```
foundry.toml        src/ (contracts)   test/ (*.t.sol)   script/ (deploy)   lib/ (deps)
```

- **Build:** `forge build`. If it fails: `forge install` (deps), `forge build --skip test`, `forge build --via-ir`, or read the exact compiler error. A non-compiling repo makes all other tool output noise — establish green first.
- **Inspect:** `forge inspect <Contract> abi`, `forge inspect <Contract> storageLayout` (crucial for proxy upgrades), `forge inspect <Contract> methods`.
- **Config:** read `foundry.toml` for `src`, `solc`, `optimizer`, `remappings`, `fuzz.runs`, `invariant.runs`.

## Tests

- **Unit / integration:** `forge test -vvv`, `--match-test <name>`, `--match-contract <name>`.
- **Fuzz:** a test function with arguments is fuzzed automatically; configure runs/depth in `foundry.toml`.
- **Invariant:** `function invariant_X() public` in a contract inheriting `Test`; `targetContract(addr)`, `targetSelector`, and handlers. Used by the fizz suite (`custom/fizz-invariants`).
- **Fork:** `forge test --fork-url $ETH_RPC_URL` (or `vm.createSelectFork`); pin with `--fork-block-number` for determinism.
- **Cheatcodes:** `vm.prank/startPrank`, `vm.deal`, `vm.warp`, `vm.roll`, `vm.expectRevert`, `vm.expectEmit`, `vm.mockCall`, `vm.load/store`, `vm.label`, `vm.snapshot/revertTo`.

## Proof-of-concept pattern

```solidity
function test_exploit() public {
    vm.createSelectFork(vm.envString("ETH_RPC_URL"), BLOCK);
    // 1. set up the attacker
    // 2. perform the exploit
    // 3. assert the profit / broken invariant
    assertGt(token.balanceOf(attacker), startBalance + EXPECTED);
}
```

## Workflow for an audit

1. `forge build` → green.
2. `forge test` → baseline (note failures; they may be in-scope bugs).
3. `forge inspect ... storageLayout` on any upgrade.
4. Write a PoC (`custom/foundry-poc`) for every High/Critical.
5. Run invariant tests for the catalog (`custom/fizz-invariants`).

## Pitfalls

- `forge build` succeeds but tests fail: check remappings and solc version.
- `--via-ir` changes gas and can change behavior; note the setting used.
- Fork tests are non-deterministic without `--fork-block-number`.
- `vm.prank` applies to the next call only; use `startPrank`/`stopPrank` for a block.
