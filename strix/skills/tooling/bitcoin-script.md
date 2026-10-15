---
name: bitcoin-script
description: Bitcoin toolchain — bitcoind -regtest and bitcoin-cli, rust-miniscript policy analysis, BDK, test vectors, and ord/runes CLIs
---

# Bitcoin (Script / Miniscript)

Bitcoin "contracts" are output scripts and spending conditions, often expressed as Miniscript policies; verification runs on `regtest` with `bitcoin-cli` and in Rust with `rust-miniscript`/BDK.

## Install / build

- `bitcoind`/`bitcoin-cli` from Bitcoin Core; check `bitcoind --version` and `bitcoin-cli --version`.
- Rust tooling: `cargo add miniscript` (`rust-miniscript`), `cargo add bdk` (Bitcoin Dev Kit), `cargo add bitcoin`.
- `ord`/`runes` CLIs (`cargo install ord`, `cargo install runes`) for ordinals and runes analysis.
- There is no compiler: scripts are assembled and decoded; use `bitcoin-cli decodescript` and the Miniscript parser.

## Core commands

```bash
# regtest node
bitcoind -regtest -daemon -fallbackfee=0.0001
bitcoin-cli -regtest createwallet "audit"
ADDR=$(bitcoin-cli -regtest getnewaddress)
bitcoin-cli -regtest generatetoaddress 101 "$ADDR"
bitcoin-cli -regtest getbalance

# inspect scripts / txs
bitcoin-cli -regtest decodescript "5121<hex>..."
bitcoin-cli -regtest decoderawtransaction <HEX>
bitcoin-cli -regtest getrawtransaction <TXID> true
bitcoin-cli -regtest importdescriptors '[{"desc":"<wpkh(...)>#checksum","timestamp":"now"}]'

# miniscript (Rust) — parse, type-check, and analyze a policy
cargo test                          # runs the crate's Miniscript test vectors
```

```rust
use miniscript::{Descriptor, Miniscript, bitcoin::Network};
let ms: Miniscript<_> = "and_v(v:pk(A),older(144))".parse().unwrap();
let desc: Descriptor<_> = "wsh(and_v(v:pk(A),older(144)))".parse().unwrap();
println!("{}", ms.max_satisfaction_weight().unwrap());
```

## Audit workflow

1. Parse the descriptor/policy with `rust-miniscript`; confirm the script type (`wsh`, `sh`, `tr`) matches intent.
2. Check timelock semantics (`older` relative vs `after` absolute) and that the spending path actually enforces them.
3. Analyze satisfaction weight and malleability (non-malleable vs legacy); a malleable script is a lead.
4. Reproduce spend conditions on `regtest`: fund, spend with the intended branch, and confirm an unauthorized branch fails — see `ecosystems/bitcoin`.
5. For ordinals/runes, inspect the envelope/commit-reveal trust and rune etching/premine rules with `ord`/`runes`.
6. Confirm High/Critical with a regtest spend PoC or a `rust-miniscript` unit test.

## Pitfalls

- `regtest` rules differ from mainnet (no real difficulty, relaxed malleability policy) — validate policy flags explicitly.
- `nLockTime`/`OP_CHECKLOCKTIMEVERIFY` use absolute vs relative (`BIP68` sequence) semantics; mixing them is a common bug.
- Miniscript type analysis passing does not mean the *policy* is safe — an anyone-can-spend branch still type-checks.
- Signature-hash flags (segwit vs legacy) change what a signature commits to; a wrong flag enables replay.
- `ord`/`runes` state is indexer-defined, not consensus; trusting an indexer's view on-chain is unsound.
