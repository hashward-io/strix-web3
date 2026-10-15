---
name: cairo-hints-and-oracles
description: Cairo/Starknet hints and oracles — syscall trust, Pragma/Pyth staleness and decimals, block timestamp reliance, call_contract/library_call targets
---

# Cairo Hints, Syscalls and Oracles

On Starknet, every value that does not come from storage or pure computation arrives through a **syscall** whose contents the sequencer/OS provides. "Hints" — off-chain-computed aid values and the syscall outputs that stand in for them — are only as trustworthy as the validation around them.

## Where to look

- **Cairo hints and off-chain aid values.** In `cairo-lang`-era code, `%{ ... %}` hints run in the prover and produce values the circuit does not constrain unless a constraint follows. In Starknet contracts the analogue is any syscall value used without a bound check. Treat every unvalidated syscall result as attacker/sequencer-influenced.
- **The syscall surface.** `starknet::syscalls::get_block_timestamp`, `get_block_number`, `get_block_hash`, `get_tx_info`, `get_caller_address`, `get_contract_address`, `get_sequencer_address`, and `storage_read_syscall`. Confirm each is used where the sequencer cannot profit from lying.
- **`get_block_timestamp` reliance.** Auctions, liquidations, vesting, and TWAP windows keyed off the raw block timestamp are manipulable by the sequencer within a window. Prefer block number where semantics allow, and always bound the delta.
- **Pragma oracle staleness.** `IPragmaOracle::get_data_median(...)` returns `price`, `decimals`, `last_updated_timestamp`, `num_sources_aggregated`, and `expiration_timestamp`. Check `last_updated_timestamp` against `get_block_timestamp` and honor `expiration_timestamp`; a missing staleness check on a value-moving consumer is a lead-to-finding.
- **Pragma decimals.** Apply `decimals` before combining `price` with a token amount; a missing scale shift is off by `10**decimals`.
- **Pyth staleness and exponent.** `IPyth::get_price_no_older_than(price_id, age, ...)` returns `PythStructs::Price { price: i64, conf: u64, expo: i32, publish_time }`. `expo` is frequently **negative** (e.g. `-8`), `conf` is a confidence band that must be bounded relative to `price`, and `publish_time` must be fresh. Feed-id confusion and wrong `expo` scaling are common.
- **Signed `i64` price / zero price.** A negative or zero `price`/`conf` from a malformed feed that a consumer does not reject can flip liquidation math.
- **Single-source dependency.** One feed, one pool, no fallback — a failure or manipulation zeroes the protocol.
- **`library_call_syscall` / `call_contract_syscall` to attacker-controlled targets.** Dispatchers (`IFooDispatcher { contract_address }`) run arbitrary code. A target read from a user parameter, or a stored address an attacker can set, lets them execute attacker logic under your call.
- **`library_call_syscall` runs foreign code in your storage.** It takes a **class hash** and executes it with *your* contract context — never point it at an unvalidated class.
- **Reentrancy via `call_contract_syscall`.** The callee gets control; state updated after the call is inconsistent during it. There is no built-in reentrancy guard.
- **`#[abi(embed_v0)]` exposure.** Every embedded component interface is externally callable. Embedding a component with oracle-admin, pause, or config setters without an owner guard exposes them. Audit the ABI, not just the contract's own impl.
- **Oracle address binding.** If the oracle address is stored at instantiation but never validated, or can be updated unguarded, the "oracle" can become the attacker.
- **`get_block_hash` trust.** It is only valid within a bounded window of recent blocks and is OS-provided; do not use it as unbiased randomness.

## Attack plan

1. Enumerate every syscall and oracle call; note which values move money or gate access.
2. For each oracle read, check freshness (`last_updated_timestamp` / `publish_time` vs block timestamp), `decimals`/`expo`, and any confidence band.
3. For each timestamp-dependent branch, ask whether the sequencer's manipulation window is enough to profit.
4. Trace every `call_contract` / `library_call` target back to its source; flag parameters and unstored addresses.
5. List embedded ABI methods; find the ones without a guard.
6. Check the oracle address lifecycle: initialized, validated, updatable only by owner.

## Proof

Use `snforge` with `starknet::testing::{set_block_timestamp, set_caller_address}` and, where available, a mock oracle to feed a stale price or a wrong `expo`. For a `call_contract` issue, deploy an attacker contract and show it executing through the vulnerable dispatch. For an embedded unguarded method, call it directly and show the privileged effect. Show concrete numbers for any value move.

## Fix

Validate every syscall-derived value against a bound. Check oracle freshness, decimals/exponent, and confidence, and prefer a manipulation-resistant feed. Do not gate value on the raw block timestamp without a bounded window. Restrict `call_contract`/`library_call` targets to validated, stored addresses and never execute a caller-supplied class hash. Embed only components whose methods are internally guarded.

## Variants and adjacent bugs

- **Stale oracle** — `last_updated_timestamp`/`publish_time` never checked.
- **Wrong `expo`/`decimals`** — a missing scale shift off by `10**n`.
- **Timestamp gating** — value moved on `get_block_timestamp` with no bound.
- **Attacker dispatcher target** — `call_contract`/`library_call` to a parameter address.
- **Embedded unguarded method** — admin reachable via `#[abi(embed_v0)]`.

## Do not flag

- Oracle reads that check freshness, decimals, and confidence.
- `call_contract` to a compile-time-constant or validated stored address.
- Documented use of block number where timestamp manipulation is irrelevant.

## Leads vs findings

- A missing staleness check is a **lead** until a value-moving consumer is shown.
- Demonstrate with a mock oracle or `set_block_timestamp` and concrete numbers.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/cairo` — syscall and ABI model.
- `tooling/cairo-scarb` — build and test commands.
- `protocols/oracles` and `vulnerabilities/oracle-manipulation` — price-feed attacks.
