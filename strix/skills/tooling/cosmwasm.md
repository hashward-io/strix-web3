---
name: cosmwasm
description: CosmWasm toolchain — wasm32-unknown-unknown builds, cw-multi-test, cosmwasm-check, cosmwasm-schema, wasmd/junod local nodes, and clippy/wasm-opt
---

# CosmWasm

CosmWasm contracts are Rust compiled to `wasm32-unknown-unknown`; `cw-multi-test` simulates a chain locally and `cosmwasm-check` validates a built artifact before deployment.

## Install / build

- Target: `rustup target add wasm32-unknown-unknown`.
- Scaffold: `cargo install cargo-generate` then `cargo generate --git https://github.com/CosmWasm/cw-template`.
- Local node: build/install `wasmd` or `junod`; check `wasmd version`.
- Optimizer: `cosmwasm-opt` (Docker) or `wasm-opt -Os`.

## Core commands

```bash
# build + test
cargo build --target wasm32-unknown-unknown --release
cargo test                          # unit tests plus cw-multi-test integration
cargo clippy --target wasm32-unknown-unknown -- -D warnings

# artifact checks / schemas
cosmwasm-check ./target/wasm32-unknown-unknown/release/my_contract.wasm
cargo run --bin schema              # writes schema/*.json via cosmwasm-schema
cosmwasm-opt ./contract.wasm -o contract.opt.wasm
wasm-opt -Os ./contract.wasm -o contract.opt.wasm

# local chain (wasmd)
wasmd init test-chain --chain-id test --home ./node
wasmd keys add alice --keyring-backend test --home ./node
wasmd add-genesis-account alice 100000000stake --home ./node
wasmd gentx alice 50000000stake --chain-id test --home ./node
wasmd start --home ./node
wasmd tx wasm store ./contract.wasm --from alice --chain-id test --gas auto -y
wasmd tx wasm instantiate <CODE_ID> '{"count":0}' --label demo --from alice --no-admin -y
wasmd query wasm contract <ADDR>
```

## cw-multi-test harness

```rust
use cw_multi_test::{App, ContractWrapper, Executor};
let mut app = App::default();
let code = app.store_code(Box::new(ContractWrapper::new(execute, instantiate, query)));
let addr = app.instantiate_contract(code, sender, &msg, &[], "demo", None).unwrap();
```

## Audit workflow

1. `cargo build --target wasm32-unknown-unknown --release`, then `cosmwasm-check` the artifact.
2. Read `instantiate`, `execute`, `query`, and `migrate` entry points and the `state.rs` layout.
3. Check `info.funds` handling, `Addr` vs `String` vs bech32 canonicalization, `Reply`/submessage ordering, and the admin/migration path — see `ecosystems/cosmwasm`.
4. Look for unbounded `range`/iteration over maps and unbounded message arrays (gas DoS).
5. Reproduce High/Critical with a `cw-multi-test` test that asserts on balances and state.
6. Run `cargo clippy` on the wasm target for lead-worthy lints.

## Pitfalls

- A contract can build for the host but fail on the wasm target (wasm-only limits; `format!`/float restrictions).
- `cosmwasm-check` validates structure, not logic; a passing check is not a safe contract.
- Addresses canonicalize differently across chains; storing `info.sender` as `String` and comparing to a bech32 literal is a common bug.
- `no-admin` at instantiate is irreversible; a missing `migrate` entry point can lock upgrades out permanently.
- `Reply` handlers run on both success and error (`reply_on` controls which); confusing the two mis-accounts state.
