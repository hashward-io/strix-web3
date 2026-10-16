---
name: move-cli
description: Move toolchain for Sui and Aptos — sui move build/test, aptos move compile/test/prove, publish/upgrade, Move Prover, and Move.toml package layout
---

# Move (Sui and Aptos)

Move is a resource-oriented bytecode language; Sui and Aptos share the syntax but differ in CLI, object model, and upgrade rules. Establish which chain a package targets before running anything.

## Install / build

- Sui: `cargo install --locked --git https://github.com/MystenLabs/sui.git sui` (or the released binary); check `sui --version`, `sui client`.
- Aptos: install script or `brew install aptos`; `aptos --version`, `aptos init`.
- Standalone Move CLI: `cargo install move-cli` (the `move` binary); `move-analyzer` via `cargo install move-analyzer`.
- Sui package layout: `Move.toml` + `sources/*.move` + `tests/*.move` + `examples/`.
- Aptos package layout: `Move.toml` + `sources/*.move`, with unit tests inline in `#[test]` modules inside the source files.

## Move.toml

```toml
[package]
name = "my_pkg"
version = "0.0.1"
upgrade_policy = "compatible"      # Sui: compatible | additive | dependency-only

[dependencies]
Sui = { git = "https://github.com/MystenLabs/sui.git", subdir = "crates/sui-framework/packages/sui-framework", rev = "framework/testnet" }

[addresses]
my_pkg = "0x0"
```

## Core commands

```bash
# Sui
sui move build
sui move test
sui move test --filter my_test
sui move new my_pkg
sui client publish --gas-budget 100000000
sui client upgrade --gas-budget 100000000 --upgrade-capability <CAP_ID>

# Aptos
aptos move compile
aptos move test
aptos move test --filter my_test
aptos move prove            # Move Prover (needs boogie + z3 on PATH; install them on demand)
aptos move build-publish-payload --json-output-file out.json
aptos move publish

# Standalone Move CLI
move build
move test
move prove
move-analyzer               # LSP

# keys / network
sui client new-address ed25519
aptos init --network devnet
```

## Audit workflow

1. Identify the chain from `Move.toml` dependencies/framework, then use the matching CLI.
2. `move build` and `move test` → green baseline; inline `#[test]` modules are often the only specification.
3. Enumerate entry points: `entry`, `public`, `public(friend)`, `public(package)` — record exactly who may call each. See `ecosystems/move`.
4. Sui: check object ownership, `transfer`, dynamic fields, and shared-object contention. Aptos: check signer capabilities and global-storage borrows.
5. Run `move prove` where specs exist; treat every spec invariant as a testable claim. The Prover is not preinstalled — `aptos move prove` needs `boogie` and `z3` on `PATH` first (`dotnet tool install --global boogie` / `pip install z3-solver` or the release binary); skip it if you cannot install them and say so.
6. Confirm High/Critical with a Move unit test or a devnet transaction.

## Pitfalls

- `public(friend)` / `public(package)` is a trust boundary; a misplaced friend function exposes internals.
- Sui `upgrade_policy` cannot be relaxed later — a `compatible` package can only add, never remove/change.
- Aptos test modules live inside sources while Sui tests live in `tests/`; searching only one misses coverage.
- `abort` codes are not exceptions; an unhandled abort from a nested call propagates and can brick a shared object.
- Resource abilities (`key`/`store`/`copy`/`drop`) govern duplication and destruction — a wrong ability is a real bug.
