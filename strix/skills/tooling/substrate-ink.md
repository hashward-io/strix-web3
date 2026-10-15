---
name: substrate-ink
description: ink!/Substrate toolchain — cargo contract build/test/check, substrate-contracts-node, ink_e2e, metadata, and wasm32 target and toolchain pinning
---

# ink! / Substrate

ink! contracts are Rust `no_std` crates compiled to `wasm32-unknown-unknown` and deployed to a Substrate `pallet-contracts` chain; `cargo-contract` is the build and deploy front-end.

## Install / build

- `rustup target add wasm32-unknown-unknown`.
- `cargo install --force --locked cargo-contract`; check `cargo contract --version`.
- Dev node: `substrate-contracts-node` — run `substrate-contracts-node --dev`.
- Pin the toolchain with a `rust-toolchain.toml` (`channel = "1.75"` etc.) so wasm builds reproduce.
- JS/Redspot: `redspot` is a Hardhat-like JS framework for Substrate contracts (`npx redspot compile`).

## Core commands

```bash
# scaffold / build
cargo contract new my_contract
cargo contract build                 # target/ink/*.contract (wasm + metadata)
cargo contract build --release
cargo contract check                 # fast type/abi check without full wasm opt
cargo contract build --skip-wasm-opt

# test
cargo test                           # host tests of contract logic
cargo test --features e2e-tests      # ink_e2e against a live node

# metadata (emitted alongside the .contract by cargo contract build)
ls target/ink/*.json

# deploy / call against a node
substrate-contracts-node --dev
cargo contract instantiate --constructor new --args 100 --suri //Alice
cargo contract call --contract <ADDR> --message flip --suri //Alice
cargo contract upload --suri //Alice
```

## ink_e2e

```rust
#[ink_e2e::test]
async fn e2e_works(mut client: ink_e2e::Client<C, E>) -> E2EResult<()> {
    let constructor = MyContractRef::new(100);
    let contract = client
        .instantiate("my_contract", &ink_e2e::alice(), constructor, 0, None)
        .await
        .unwrap();
    let res = client
        .call("my_contract", &ink_e2e::alice(), contract.call().get())
        .await
        .unwrap();
    assert!(res.is_ok());
    Ok(())
}
```

## Audit workflow

1. `cargo contract build` → `.contract` and `metadata.json`; `cargo test` for the baseline.
2. Enumerate `#[ink(message)]` / `#[ink(constructor)]`, their `#[ink(payable)]`, and any `#[ink(selector = ...)]`.
3. Check origin handling and `ensure_signed`, plus whether `#[ink(payable)]` sits on messages that should be free — see `ecosystems/substrate`.
4. Review storage layout/packing (`#[ink(storage)]`, `Mapping`, `Lazy`) and `Weight` annotations.
5. Trace contract→contract calls for reentrancy (see `vulnerabilities/reentrancy`).
6. Confirm High/Critical with `ink_e2e` or a host test.

## Pitfalls

- `cargo test` exercises host-native code, which differs from wasm semantics (no floats, wasm limits, trap behavior).
- Unpinned toolchains break `ink_e2e` compatibility with a running node's contract version.
- `#[ink(payable)]` missing on a value-receiving message reverts transfers; present where it should not be traps value.
- Storage-layout changes break live contracts; never reorder or remove fields on a deployed contract.
- `Mapping` does not support iteration; bugs arise from auxiliary index vectors that drift out of sync.
