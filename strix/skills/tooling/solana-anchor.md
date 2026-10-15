---
name: solana-anchor
description: Solana program toolchain — cargo build-sbf, anchor build/test, solana-test-validator, LiteSVM, Trident fuzzing, and program deploy for Rust audits
---

# Solana (Anchor / native)

Solana programs are Rust SBF binaries; `anchor` wraps the build/test/deploy loop while `solana-test-validator`, LiteSVM, and Trident provide fast local execution and fuzzing.

## Install / build

- Toolchains: `sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"` for the Agave/Solana CLI; `cargo install --git https://github.com/coral-xyz/anchor avm --force && avm install 0.30.1 && avm use 0.30.1`.
- SBF compiler ships with the SDK; standalone `cargo-build-sbf --version`.
- Anchor does not need `rustup target add`; it invokes `cargo build-sbf` for the on-chain artifact.
- `rust-toolchain.toml` pins the Rust version Anchor uses — match it exactly or builds drift.

## Core commands

```bash
# build
anchor build                      # emits target/deploy/*.so and target/idl/*.json
cargo build-sbf                   # native build without IDL
anchor build --verifiable         # reproducible docker build

# test
anchor test                       # starts a validator, deploys, runs ts/mocha + cargo tests
anchor test --skip-local-validator  # reuse an already-running validator
anchor test --skip-build          # reuse existing artifacts
cargo test                        # host-side unit tests only

# local validator + logs
solana-test-validator --reset
solana config set --url http://127.0.0.1:8899
solana airdrop 100
solana logs <PROGRAM_ID>          # stream program logs and compute units
solana program show <PROGRAM_ID>

# deploy
solana program deploy target/deploy/myprog.so
anchor deploy
anchor keys sync                  # fix declare_id! vs target/deploy keypair mismatch

# LiteSVM (fast in-process tests)
cargo add --dev litesvm

# fuzzing
cargo install --git https://github.com/Ackee-Blockchain/trident trident-cli
trident init && trident fuzz run fuzz-0
cargo +nightly fuzz run <target>  # cargo-fuzz, if the program is a lib crate

# SPL tokens / Token-2022
spl-token create-token --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb
spl-token create-account <MINT>
spl-token mint <MINT> 1000
```

## Audit workflow

1. `anchor build` → green, then `anchor test` as the baseline; failures may be in-scope bugs.
2. Read `anchor.toml`, `declare_id!`, and `target/idl/*.json` to enumerate instructions and accounts.
3. Trace each instruction's account validation (`Account<'info, T>`, `Signer<'info>`, `#[account(...)]` constraints) — see `ecosystems/solana` and `vulnerabilities/solana-cpi-safety`.
4. For every CPI, confirm the program id, signer seeds, and account mutability.
5. Reproduce High/Critical with a LiteSVM or Mocha test; use Trident for arithmetic and account fuzzing.

## Pitfalls

- `anchor test --skip-local-validator` fails if the running validator lacks the program — deploy first.
- A `declare_id!` vs keypair mismatch silently deploys to a different address; run `anchor keys sync`.
- Compute-unit and rent limits differ from mainnet; a passing local test can OOM on-chain.
- Token-2022 mints require the extension program id; default `spl-token` targets legacy Token.
- Host `cargo test` does not check SBF-only constraints (stack, heap, CU).
