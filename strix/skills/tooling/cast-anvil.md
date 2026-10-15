---
name: cast-anvil
description: cast and anvil — query chain state, decode calldata, simulate calls, and run a local fork for manual exploration
---

# cast and anvil

`cast` reads and writes chain state from the shell; `anvil` runs a local node. Together they let you explore a live protocol without writing a test.

## cast — read and inspect

- **Chain/state:** `cast block-number`, `cast block latest`, `cast balance <addr>`, `cast nonce <addr>`, `cast code <addr>` (is there a contract?).
- **Calls:** `cast call <to> "<sig>(<types>)" <args> --rpc-url $ETH_RPC_URL` — read a view function.
- **Storage:** `cast storage <addr> <slot>` — read a raw slot; `cast index <type> <key> <slot>` for mapping slots.
- **Decode:** `cast 4byte <selector>`, `cast decode-calldata "<sig>" <data>`, `cast --to-hex`, `cast --to-dec`, `cast --to-unit`, `cast --from-wei`.
- **ABI:** `cast interface <addr>` / `cast abi-decode` / `cast abi-encode`.
- **Tx:** `cast tx <hash>`, `cast receipt <hash>`, `cast logs --from-block ... --address ...`.
- **Signatures:** `cast sig "<fn>"`, `cast keccak`, `cast wallet`.
- **Simulate:** `cast call --from <addr> ...` to check a call as a specific sender; `cast run <txhash>` to replay a transaction with a trace.

## anvil — a local fork

- `anvil --fork-url $ETH_RPC_URL --fork-block-number <N>` → a local node whose state is a frozen fork.
- `anvil --fork-url $ETH_RPC_URL` then use `cast` against `http://127.0.0.1:8545`.
- Cheat RPC methods: `anvil_impersonateAccount`, `anvil_setBalance`, `anvil_setStorageAt`, `anvil_mine`, `anvil_setNextBlockTimestamp`.
- Use it to: reproduce a live exploit manually, test a call as a whale, inspect state at a specific block, and then codify the finding as a Foundry PoC.

## Audit workflow

1. `cast code <target>` — confirm a contract exists (a `.call` to an EOA returns success, which can hide a bug).
2. `cast interface <target>` — get an ABI to call it.
3. Read storage (`cast storage`) to inspect internal accounting a getter does not expose.
4. Reproduce the suspect sequence with `anvil` + `cast`, then port it to a Foundry test.

## Pitfalls

- Public RPCs rate-limit; use `--rpc-url` with a keyed endpoint for heavy work.
- `cast call` on a state-changing function may revert or not reflect a real tx (no state change) — use `--trace` or a fork.
- Storage slot layout must match the contract's actual layout (use `forge inspect storageLayout`).
