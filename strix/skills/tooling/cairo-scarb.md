---
name: cairo-scarb
description: Cairo/Starknet toolchain — scarb build/test, snforge and sncast (starknet-foundry), devnet, cairo-lint, amarna/caracal, and Scarb.toml layout
---

# Cairo (Scarb / Starknet Foundry)

Cairo compiles to Sierra and then CASM for Starknet; `scarb` is the build and package manager, and Starknet Foundry (`snforge`) is the test runner.

## Install / build

- `curl -L https://raw.githubusercontent.com/software-mansion/scarb/main/install.sh | sh`; `scarb --version`.
- Starknet Foundry: `curl -L https://raw.githubusercontent.com/foundry-rs/starknet-foundry/master/scripts/install.sh | sh`; check `snforge --version` and `sncast --version`.
- Devnet: `cargo install starknet-devnet` (the Rust `starknet-devnet-rs`); run with `starknet-devnet --seed 0`.
- Analyzers: `cairo-lint` (`scarb cairo-lint` or the `cairo-lint` binary), `amarna` (`pip install amarna`), `caracal` (`cargo install caracal`).
- `universal-sierra-compiler` compiles Sierra → CASM: `universal-sierra-compiler compile contract.sierra.json`.

## Scarb.toml

```toml
[package]
name = "my_contract"
version = "0.1.0"
edition = "2023_11"

[dependencies]
starknet = "2.6.0"

[dev-dependencies]
snforge_std = "0.20.0"
assert_macros = "2.6.0"

[[target.starknet-contract]]
sierra = true

[tool.snforge]
fuzzer_runs = 1000
```

## Core commands

```bash
# build / format
scarb build
scarb fmt
scarb test                 # runs the configured test runner (snforge)

# Starknet Foundry tests
snforge init my_proj
snforge test
snforge test --filter my_test
snforge test --fuzz-runs 1000

# declare / deploy to a node
sncast account create --network devnet --name acct
sncast account deploy --network devnet --name acct
sncast declare --network devnet --contract-name MyContract
sncast deploy --network devnet --class-hash 0x... --constructor-calldata 0x...

# local devnet
starknet-devnet --seed 0 --port 5050

# static analysis
cairo-lint .
amarna .
caracal .
```

## Audit workflow

1. `scarb build` → Sierra artifacts; `scarb test` or `snforge test` for the baseline.
2. Enumerate `#[external(v0)]`, `#[l1_handler]`, and `#[constructor]` functions and their access control.
3. Check `felt252` arithmetic (overflow only in specific ops), `u256`/`i128` conversions, and `starknet::ContractAddress` checks — see `ecosystems/cairo` and `hacking_agents/math-precision`.
4. Inspect storage: the `#[storage]` layout, legacy `LegacyMap` aliasing, and storage-address collisions.
5. Run `cairo-lint`, `amarna`, and `caracal` as lead generators, then verify each by hand.
6. Reproduce High/Critical with an `snforge` test or a `sncast` transaction against devnet.

## Pitfalls

- `scarb build` emits Sierra, not CASM; deployment needs `universal-sierra-compiler` or a node that compiles it.
- `felt252` division truncates and does not revert; range assumptions must be asserted explicitly.
- `snforge` fuzzing uses random inputs — add boundary seeds or the interesting cases may never run.
- `#[l1_handler]` functions are callable from L1 with a forged `from_address` if it is not validated.
- Legacy `LegacyMap` can collide with new `Map` storage addresses; mixed codebases need care.
