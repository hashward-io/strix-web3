---
name: sway-fuel
description: Sway/Fuel toolchain — forc build/test/deploy/fmt/doc, fuel-core run, fuelup toolchain manager, fuels-rs tests, and predicate/script deployment
---

# Sway (Fuel)

Sway is a Rust-inspired language for the FuelVM with four program kinds: contracts, scripts, predicates, and libraries. `forc` is the package and build tool and `fuel-core` is the node.

## Install / build

- `curl https://install.fuel.network | sh` installs `fuelup`; then `fuelup toolchain install latest`; check `forc --version`.
- `fuelup component add forc-wallet`; `forc-wallet` manages keys.
- Node: `fuel-core run --db-type in-memory` (or with a persistent db path).
- Integration tests: `fuels-rs` or `fuels-ts`; `cargo add fuels` in a test crate.

## Forc.toml / layout

```toml
[project]
authors = ["you"]
entry = "main.sw"
license = "Apache-2.0"
name = "my_contract"

[dependencies]
```

- Layout: `Forc.toml`, `src/main.sw`, `tests/` (Rust `fuels-rs` tests), `out/` (artifacts).

## Core commands

```bash
# build / format / docs
forc build
forc build --release
forc fmt
forc doc

# test
forc test                         # in-language #[test] modules
cargo test                        # fuels-rs integration tests in tests/

# deploy (contracts)
forc deploy --node-url http://127.0.0.1:4000 --gas-price 0
forc deploy --testnet

# scripts & predicates
forc run --node-url http://127.0.0.1:4000 script
forc predicate-root               # predicate address from bytecode

# local node + wallet
fuel-core run --db-type in-memory --port 4000
forc wallet account new
forc wallet sign --account 0 tx.json
```

## Audit workflow

1. `forc build` and `forc test` → green baseline; the Rust `tests/` under `fuels-rs` are usually the richest.
2. Identify the program kind: predicates cannot write storage, so a predicate that reads a storage variable is a bug — see `ecosystems/sway`.
3. Check `msg_sender()`, `AssetId` comparisons, and `msg_amount()` — missing sender checks and asset-id confusion are top classes.
4. Inspect arithmetic: Sway has checked (`+`) vs wrapping (`overflowing_*`) paths, and tests that assume wrap.
5. Trace external calls for reentrancy and reentrancy through scripts.
6. Confirm High/Critical with a `forc test` or a `fuels-rs` test against `fuel-core`.

## Pitfalls

- Predicates are stateless; relying on storage or on a mutable UTXO across spends is unsound.
- The base-asset `AssetId` vs a custom asset is a common spoofing vector.
- `forc deploy` to testnet needs a funded wallet; a local `fuel-core` needs a genesis coin.
- Artifacts in `out/` can be stale — rebuild before testing.
- Sway's `#[test]` runs in the Sway VM while `fuels-rs` runs against a node; they can disagree on gas and state.
