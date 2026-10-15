---
name: stylus
description: Arbitrum Stylus toolchain — cargo stylus new/check/build/export-abi/deploy/verify, stylus-sdk, sol_storage!, nitro-devnode, and cast interaction
---

# Arbitrum Stylus

Stylus lets Rust (compiled to WASM) run on Arbitrum alongside Solidity, sharing the same address space and EVM storage; `cargo-stylus` is the build and deploy front-end.

## Install / build

- `rustup target add wasm32-unknown-unknown`.
- `cargo install --force cargo-stylus`; check `cargo stylus --version`.
- Latest: `cargo install --force cargo-stylus --git https://github.com/OffchainLabs/cargo-stylus`.
- Local node: `nitro-devnode` (Docker) on port `8547`; `cast` (Foundry) for interaction.
- SDK: the `stylus-sdk` crate plus `#[stylus_sdk::contract]` and `sol_storage!`.

## Core commands

```bash
# scaffold / build
cargo stylus new my_project
cargo stylus check --endpoint http://localhost:8547
cargo stylus build --features export-abi
cargo stylus export-abi                 # Solidity interface for the wasm contract

# deploy / verify
cargo stylus deploy --endpoint http://localhost:8547 --private-key $PK
cargo stylus deploy --endpoint https://stylus-testnet.arbitrum.io/rpc --private-key $PK
cargo stylus verify --deployment-tx <TX> --endpoint <RPC>
cargo stylus cache bid <ADDRESS> 0      # cache the contract to lower activation cost

# devnode + cast
nitro-devnode                           # local chain at :8547
cast rpc --rpc-url http://localhost:8547 eth_chainId
cast call <ADDR> "greeting()(string)" --rpc-url http://localhost:8547
cast send <ADDR> "setGreeting(string)" "hi" --private-key $PK --rpc-url http://localhost:8547
```

## Contract skeleton

```rust
#[stylus_sdk::contract]
mod my_contract {
    use stylus_sdk::{alloy_primitives::U256, prelude::*};
    sol_storage! { #[entrypoint] pub struct Counter { uint256 number; } }
    #[public] impl Counter {
        pub fn number(&self) -> U256 { self.number.get() }
        pub fn set_number(&mut self, n: U256) { self.number.set(n); }
    }
}
```

## Audit workflow

1. `cargo stylus check` and `cargo stylus build` → wasm; run `cargo stylus export-abi` and diff the ABI against intent.
2. Map `sol_storage!` slots to EVM storage; Solidity↔Stylus storage-layout mismatches are a top bug class (see `ecosystems/evm`).
3. Check `#[payable]`, `msg::sender()`/`msg::value()`, and cross-contract calls back into Solidity.
4. Confirm the wasm is under the 24KB compressed size and activation gas limits.
5. Reproduce High/Critical with a `cast` sequence against `nitro-devnode`, or a Foundry fork test (see `tooling/foundry`, `tooling/cast-anvil`).
6. `cargo stylus verify` proves on-chain bytecode matches the local build.

## Pitfalls

- A contract passing `check` locally may exceed on-chain size/activation limits on a different chain.
- Rust panics abort differently from Solidity reverts; error strings may be lost across the boundary.
- `sol_storage!` packing is not identical to Solidity's; reading a Solidity-written slot from Stylus can mis-decode.
- `sol!`/ABI encoding in the SDK must match the exported ABI or callers send the wrong selector.
- Stylus contracts pay activation rent; an underfunded contract can be deactivated mid-protocol.
