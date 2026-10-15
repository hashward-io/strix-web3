---
name: near
description: NEAR toolchain — cargo near build/test, near-cli and near-cli-rs, near-workspaces sandbox, near-sandbox, wasm32 builds, and mock testing
---

# NEAR

NEAR contracts are Rust (or AssemblyScript) compiled to `wasm32-unknown-unknown`; async cross-contract calls return Promises, which is where most bugs live.

## Install / build

- `rustup target add wasm32-unknown-unknown`.
- `cargo install cargo-near`; check `cargo near --version`.
- CLI: legacy `npm install -g near-cli` or the rewrite `cargo install near-cli-rs` (the `near` binary).
- Sandbox: the `near-sandbox` binary (`cargo install near-sandbox` or download) plus the `near-workspaces` crate for tests.
- `cargo test` runs host unit tests against a mocked blockchain environment.

## Core commands

```bash
# build / test
cargo near build                    # produces target/near/*.wasm
cargo near build --release
cargo test                          # host tests (mock env)
cargo test --features unit-test
cargo near test                     # workspace-level tests

# deploy / call (near-cli-rs)
near create-account my.testnet --useFaucet
near deploy my.testnet target/near/my_contract.wasm
near call my.testnet method '{"k":"v"}' --accountId my.testnet
near view my.testnet get_value '{}'
near state my.testnet

# legacy near-cli
near deploy --accountId my.testnet --wasmFile ./target/near/my_contract.wasm

# local sandbox
near-sandbox --home /tmp/near-sandbox        # spawns a local RPC
near state my.testnet --nodeUrl http://127.0.0.1:3030
```

## near-workspaces test

```rust
use near_workspaces::types::NearToken;
let worker = near_workspaces::sandbox().await?;
let wasm = std::fs::read("target/near/my_contract.wasm")?;
let contract = worker.dev_deploy(&wasm).await?;
contract.call("set").args_json(serde_json::json!({"v": 1})).transact().await?;
```

## Audit workflow

1. `cargo near build` and `cargo test` → green baseline; note mock-vs-sandbox differences.
2. Enumerate `#[near_bindgen]` methods and their `#[payable]` attribute and `&self`/`&mut self` mutability.
3. Check `predecessor_account_id()` vs `signer_account_id()` — the classic spoof (see `ecosystems/near`).
4. Audit async: which Promise results are awaited, whether callbacks validate the caller, and whether the 1-yoctoNEAR deposit is enforced on `transfer`/`ft_transfer`.
5. Check storage staking/deposit accounting and unbounded iteration over `UnorderedMap`.
6. Confirm High/Critical with a `near-workspaces` sandbox test asserting balances and panics.

## Pitfalls

- Host `cargo test` uses a mock runtime; Promise scheduling and gas differ on-chain — prefer the sandbox for cross-contract tests.
- wasm size and gas limits differ from host; a passing unit test can exceed on-chain limits.
- A callback method is publicly callable; if it trusts the predecessor it is exploitable directly.
- `#[payable]` missing on a deposit method rejects attached NEAR; present where unintended can strand funds.
- `--features` gating host test modules is easy to get wrong; a skipped test module looks like a pass.
