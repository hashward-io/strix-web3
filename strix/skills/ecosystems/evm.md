---
name: evm
description: EVM ecosystem playbook — Solidity 0.4–0.8, Vyper, Yul/Huff, Stylus; Foundry/Hardhat builds; EVM bug-class map and L2 differences
---

# EVM Ecosystem

The EVM is a stack machine with 256-bit words, persistent storage, and a message-call model. Most deployed value lives here, and most audit time is spent in it. This playbook maps the language surfaces, the build systems, and the chain-family differences you must account for before trusting a trace.

## When to use

- Any Solidity, Vyper, Yul, Huff, or Arbitrum Stylus target.
- A deployed `0x…` address or a repo with `foundry.toml` / `hardhat.config.*`.
- You need the base-layer bug-class map before narrowing to a `protocols/` or `vulnerabilities/` skill.

## Languages and version semantics

- **Solidity `^0.8`:** checked arithmetic (overflow reverts); `unchecked { }` opts out. **Below 0.8:** all arithmetic wraps silently — treat every `+ - *` as suspect. See `tooling/solidity`.
- **Solc 0.8.x specifics:** transient storage (0.8.24+, `tstore`/`tload`), `bytes.concat`, `abi.encodeCall`, custom errors, `immutable` (bytecode, not storage), and `unchecked` blocks after a proven bound.
- **Vyper:** Python-like; `@external`/`@internal`, `@payable`, `@nonreentrant`. 0.3.x vs 0.4.x change default visibility and the `@nonreentrant` key. Bounds are checked by default; the `unsafe_*` intrinsics are where bugs hide.
- **Yul / inline assembly:** no type or bounds checks. Watch `mstore`/`mload` offsets, `returndatasize`, free-memory-pointer misuse, and unchecked `call` return values.
- **Huff:** raw opcode macros. Bugs are stack depth, `calldata` layout, and a missing `revert` path.
- **Arbitrum Stylus (Rust → WASM):** contracts are WASM but call the EVM via the host; watch `msg::value`, storage cache coherency (`flush_cache`), `#[payable]`/`#[nonpayable]`, and gas metering differences. Rust arithmetic is checked in debug and wraps in release unless `overflow-checks = true`.

## Toolchain & build

- **Foundry:** `forge build`, `forge test`, `foundry.toml`. Primary. See `tooling/foundry`.
- **Hardhat:** `npx hardhat compile`; check the solc version and optimizer settings pinned per file.
- **Vyper:** `vyper contract.vy`, or the `titanoboa` test harness.
- **Stylus:** `cargo stylus build`, then `cargo stylus check`.
- `cast call`/`cast storage`/`cast 4byte`; `anvil` for local forks (`tooling/cast-anvil`).
- Static: `slither .` (`tooling/slither`), `aderyn` (`tooling/aderyn`), `mythril` for symbolic execution.
- Fuzz: `echidna` (`tooling/echidna`), `medusa` (`tooling/medusa`). Formal: `halmos` (`tooling/halmos`).
- Decompilers for unverified bytecode: `heimdall-rs`, `panoramix`.
- Establish a **green build** first; a non-compiling repo makes every analyzer output noise.

## Where the bugs live

Map each surface to its bug class; severity vocabulary is exactly Critical/High/Medium/Low/Informational.

- **Reentrancy / callbacks:** state written after an external `call`; ERC-777/1155/721 hooks; flash-loan callbacks; read-only reentrancy via a view a peer consumes → `vulnerabilities/reentrancy`.
- **Access control:** missing modifiers, `tx.origin`, unguarded initializer, `delegatecall` into an attacker target → `vulnerabilities/access-control`, `hacking_agents/access-control`.
- **Oracle / price:** spot reserves or `slot0` used as a price; missing TWAP; stale `latestRoundData` → `vulnerabilities/oracle-manipulation`.
- **Precision / rounding:** `divide-before-multiply`, truncation, decimal mismatch (`1e18` on an `e6` token), rounding against the protocol → `vulnerabilities/precision-rounding`.
- **Accounting / conservation:** balances vs internal ledgers diverge; fee-on-transfer and rebasing tokens → `vulnerabilities/accounting-conservation`, `vulnerabilities/token-integration`.
- **Flash loans:** any invariant that holds only without atomic capital → `vulnerabilities/flash-loan-attacks`.
- **Signatures:** missing nonce/chainId/deadline, `ecrecover` malleability, EIP-712 domain confusion → `vulnerabilities/signature-replay`.
- **Upgradeability:** storage-slot collision, uninitialized implementation, missing `_disableInitializers`, selector clash → `vulnerabilities/upgradeability-proxy`.
- **Unchecked returns:** low-level `call` success ignored; ERC-20 `transfer`/`approve` bool ignored → `vulnerabilities/unchecked-returns`.
- **ERC-4626 inflation:** first-depositor share inflation, donation attack → `vulnerabilities/erc4626-inflation`.
- **DoS / griefing:** unbounded loops, push-payment to a reverting recipient, gas-limit assumptions → `vulnerabilities/dos-griefing`.
- **MEV:** missing slippage/deadline; sandwichable transitions → `vulnerabilities/mev-frontrunning`.
- **Governance:** flash-loanable voting power, proposal threshold, timelock bypass → `vulnerabilities/governance-attacks`.
- **Cross-contract consistency:** two contracts disagree on shared state → `vulnerabilities/cross-contract-consistency`.

## Chain-family differences

- **L2 rollups (Arbitrum, Optimism, Base, zkSync):** `block.number` semantics differ; Optimism aliases `tx.origin`/`msg.sender` for L1 senders; Arbitrum's `block.timestamp` is sequencer-controlled at second granularity; gas accounting and `gasleft()` differ from L1.
- **Precompiles:** L2 precompiles (Arbitrum `arb*`, Optimism `L1Block`) carry their own trust assumptions; a `staticcall` to an unknown address can succeed with empty data.
- **EIP-1153 transient storage:** `tstore`/`tload` clear per transaction; a lock in transient storage has different scope than a storage lock — verify the guard survives the nested call chain you care about.
- **EIP-7702 (set-code accounts):** an EOA can delegate to contract code within a tx; any auth model that trusted "EOA cannot run code" or a fixed `tx.origin` breaks.
- **`block.chainid`:** used in signatures; a forked chain reusing a chainId is a replay surface.

## Proof standard

A **Foundry fork PoC** pinned to a block (`vm.createSelectFork(vm.envString("ETH_RPC_URL"), BLOCK)`) that performs the exploit and asserts profit or the broken invariant with concrete numbers. See `custom/foundry-poc`. Where a fork is impossible, a mock-based unit test plus a complete reachable trace is the floor for High/Critical. Anything less is a **lead**.

## Testing

- `forge test --fork-url $ETH_RPC_URL --fork-block-number <n>` for deterministic forks.
- Invariant suites (`targetContract`, handlers) for conservation laws — see `custom/fizz-invariants`, `analysis/invariant-discovery`.
- `echidna` / `medusa` for property fuzzing; `halmos` for symbolic proofs of a bound.
- Differential tests when a reference implementation exists.

## Fix patterns

Checks-effects-interactions plus a reentrancy guard scoped to every state-sharing entry; explicit roles (`AccessControl`/`Ownable`); pull-payments; `SafeERC20`; `mulDiv` with rounding toward the protocol; TWAP or Chainlink with staleness checks; `initializer` + `_disableInitializers()`; storage gaps for upgrades; bounded loops with pagination.
