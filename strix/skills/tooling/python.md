---
name: python
description: Python in the sandbox — scripting, web3/eth-abi, decoding transactions, and computing exploit inputs
---

# Python (Web3 Scripting)

Python in the sandbox is for arithmetic, decoding, and orchestration the shell tools do not cover. All heavy lifting should end in a Foundry PoC; Python gets you there faster.

## Common libraries

- `web3` (`from web3 import Web3`) — `Web3.to_checksum_address`, `Web3.keccak`, `w3.eth.call`, `w3.eth.get_storage_at`, contract ABIs.
- `eth_abi` — `decode(['uint256','address'], data)`, `encode(...)`.
- `eth_utils` — `to_wei`, `from_wei`, `keccak`, `to_hex`.
- `vyper`/`solc-select` — only if the target uses them.
- Standard library for math: use Python's arbitrary-precision ints to compute exact values a Solidity division would truncate.

## Useful tasks

- **Decode a transaction** — fetch calldata with `cast tx`/`cast receipt`, split the selector, decode with `eth_abi`; identify which function and with what args an exploit used.
- **Compute a boundary** — find the exact input where a rounding error flips (e.g. the smallest `x` with `x * totalSupply / totalAssets == 0`) using Python ints, then feed it to a Foundry test.
- **Storage inspection** — read raw slots (`cast storage`), apply the layout from `forge inspect storageLayout`, and reconstruct internal accounting.
- **Batch RPC** — pull logs/events across a range to reconstruct a historical exploit.
- **Generate handlers** — emit Solidity handler functions from the invariant catalog for the fizz suite.

## Rules

- **Do not run network calls against the target protocol as the "test."** Reproduce in a Foundry fork; Python is for analysis and input generation.
- Print exact integers (no floats) when reasoning about on-chain math.
- Write scripts under the run's working directory so they are part of the evidence.

## Pitfalls

- `float` in Python does not match fixed-point on-chain; use `int` everywhere.
- Checksum addresses matter for `web3`; use `Web3.to_checksum_address`.
- RPC rate limits; batch and cache.
