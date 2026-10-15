---
name: near-access-and-math
description: NEAR access and math — predecessor vs signer account id, missing owner/access-key checks, 1-yoctoNEAR guards, release-vs-debug overflow, unwrap panics, and refund handling
---

# NEAR Access and Math

NEAR distinguishes the immediate caller (`predecessor_account_id`) from the transaction signer (`signer_account_id`); conflating them, skipping an access check, or trusting a debug-only overflow check is how contracts get drained or bricked.

## Where to look

- Identity: `env::predecessor_account_id()` (the caller — may be a contract) versus `env::signer_account_id()` (the tx signer). Owner checks and callback checks usually need one, not the other.
- Auth: `assert_eq!(predecessor, owner)`, `assert_one_yocto()` / `assert_at_least_one_yocto()`, and access-key management (`add_access_key`, `delete_key`, `add_full_access_key`).
- Deposits: `env::attached_deposit()` compared against `yoctoNEAR(1)` for the standard "require a full access key" pattern.
- Arithmetic: `checked_add`, `saturating_*`, `overflowing_*` versus raw `+`/`-`/`*`; build profile (`--release`, `overflow-checks`).
- Panics: `.unwrap()`, `.expect()`, `panic!`, and array indexing on caller-supplied input.
- Refunds: `Promise::new(env::predecessor_account_id()).transfer(excess)`.

## Attack plan

1. Identity confusion: a privileged method checks `signer_account_id()` for the owner. Through a cross-contract call, a contract can be the predecessor while the signer is the owner — or the reverse. Decide which identity the check truly wants and test the other path.
2. Callback/relayer trust: a method trusting `predecessor_account_id()` as "the user" when the predecessor can be an arbitrary contract the attacker controls (calls your contract on their behalf).
3. Missing access check: a state-mutating method with no owner guard, or one that relies on `assert_one_yocto()` alone. The 1-yocto check only proves the caller has a *full access key* to the calling account — it is not an owner check. Verify the caller is the intended account.
4. Access-key management: a method that adds a full-access key for `predecessor_account_id()` because it assumed the caller is the owner; combined with a weak guard, an attacker adds themselves as a full-access key.
5. Overflow: build with release/`overflow-checks = false` and a raw subtraction or multiplication. A wrapped `balance - amount` mints balance; a wrapped `amount * price` undercharges.
6. `unwrap`/panic DoS: parsing caller-supplied JSON with `unwrap()`, indexing a `Vec` with a caller index, or `u128` division by zero — any of these panics and reverts. If reachable in a shared code path, it is a griefing/DoS.
7. Refund handling: a payable method that accepts more than required and never refunds strands funds; or refunds to `signer` instead of `predecessor`, sending the refund to the wrong account.

## Proof

- `near-workspaces` test: use two accounts and a malicious caller contract; call the guarded method with a spoofed predecessor/signer relationship and assert the unauthorized mutation.
- `near-sdk` unit test with `VMContextBuilder::signer_account_id` and `predecessor_account_id` set independently.
- For overflow, build in release and assert the wrapped result (or a minted balance).
- For panic DoS, pass malformed input and show the revert in a shared path.

## Fix

- Use the right identity: `predecessor_account_id()` for "who called me", `signer_account_id()` for "who signed", and check ownership explicitly against the intended account.
- Guard every privileged method with an explicit owner check; never treat `assert_one_yocto()` as authorization by itself.
- Restrict access-key management to verified owners; never add a key for an unverified predecessor.
- Use `checked_*`/`saturating_*` arithmetic and enable `overflow-checks` in release; validate divisors.
- Replace `unwrap()`/`expect()` on external input with checked handling and explicit errors.
- Refund excess deposit to the correct account and document the deposit contract.

## Identity and math quick reference

- On a plain transaction `predecessor_account_id() == signer_account_id()`; they differ on cross-contract calls.
- `assert_one_yocto()` requires exactly 1 yocto attached — it proves a full access key, not ownership.
- `near_sdk::env::attached_deposit()` is the attached amount; `yoctoNEAR(n)` converts to yocto units.
- Release builds may wrap on overflow unless `overflow-checks = true` is set in the release profile.
- `near_sdk::Promise::new(predecessor).transfer(amount)` refunds; the transfer is asynchronous.

## Severity and finding bar

- An identity-confusion bypass of an owner/authority check is **Critical**.
- A wrapped underflow or over-mint is **Critical**.
- A panic DoS on a shared path is **Medium** to **High**.
- A non-refunded surplus deposit that strands user funds is **Medium**.

## See also

- `ecosystems/near` — the ecosystem playbook.
- `vulnerabilities/access-control`, `vulnerabilities/precision-rounding` — the general classes.
- `near-promise-and-storage` — the sibling NEAR surface.
