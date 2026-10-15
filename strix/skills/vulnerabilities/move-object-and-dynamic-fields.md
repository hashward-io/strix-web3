---
name: move-object-and-dynamic-fields
description: Move/Sui object and dynamic-field bugs - owned/shared/immutable ownership, shared-object contention, dynamic field aliasing, Table/Bag key confusion, transfer::share_object, UID vs ID
---

# Object & Dynamic-Field Semantics (Sui Move)

Sui objects are typed, owned values. *How* an object is owned (owned / shared / immutable) and
*how* it is keyed in dynamic storage determine who can touch it, in what order, and whether two
references alias. Mistaking one for another is a recurring class of bug.

## Where to look

- **Object ownership mode** — `transfer::transfer` (owned by one address), `transfer::share_object`
  (shared, mutable by anyone via consensus), `transfer::freeze_object` (immutable). The public
  variants `public_transfer`, `public_share_object`, `public_freeze_object` require `T: key + store`
  and are callable by any module. A resource that should be owned but is `shared` can be driven by
  anyone; one that should be immutable but is `shared` can be mutated.
- **Shared-object contention & ordering** — a shared object serializes all transactions touching
  it; a long/aborting transaction on a shared object delays or starves others (DoS). Ordering is
  by consensus, not caller — logic that assumes "my transaction runs before yours" on a shared
  object is wrong (front-runnable). Owned objects give single-writer ordering; shared do not.
- **Dynamic field aliasing** — `dynamic_field::add<T, V>`, `borrow`, `borrow_mut`, `remove`,
  `exists_`, and the object variants `dynamic_object_field::*`. The field key is `(TypeName<T>, K)`;
  a field can be shadowed/overwritten if the same `T`/`K` pair is re-added, and reading via the
  wrong `T` (a different phantom type) misses or mis-reads it. `dynamic_object_field` stores an
  object id and enforces `V: key`, unlike plain `dynamic_field`.
- **`Table`/`Bag` key confusion** — `sui::table::Table<K, V>` keys on the concrete `K` type;
  `sui::bag::Bag` keys on `TypeName` of the key type (so the same bytes under different types are
  distinct). `ObjectTable`/`ObjectBag` store object ids. Passing a key of the wrong type, or using
  a `bag` where a `table` was intended, silently misses. Iterating a bag is order-independent.
- **`transfer::share_object` trust** — once shared, *any* module holding a `&mut` to it can mutate
  fields; there is no per-field access control. If a shared object holds an `AdminCap` field or a
  `Balance`, every public function that takes `&mut` can reach it.
- **`object::id` vs `uid` confusion** — `sui::object::UID` is the field (`id: UID`); the actual
  `ID` is `uid.to_inner()` / `object::id<T>(t)` / `object::id_from_address(addr)`. Comparing a
  `UID` to an address, or using `uid` where an `ID` is required, misidentifies the object. `UID`
  must be `delete`d on object destruction (`object::delete`); a stale `UID` reused as an identity
  is unsafe.
- **`ID` derivation** — `ID` is derived from the first transaction's digest + index; an attacker
  cannot choose it, but logic that assumes a predictable `ID` is wrong.

## Attack plan

1. For each object type, classify its ownership (owned/shared/immutable) and whether that matches
   the trust model.
2. For shared objects, list every `public`/`entry` function taking `&mut` and what it can mutate;
   look for starvation and front-running.
3. Re-key each dynamic field: is the `(T, K)` pair unique, and is every read using the same `T`/`K`
   as the write?
4. Distinguish `Table` vs `Bag` vs `ObjectTable` at each use.
5. Trace `uid`/`ID` usage: correct accessor, correct comparison type, `object::delete` on destroy.

## Proof

- Sui: `sui move test`. For aliasing, add a dynamic field under one `TypeName` and read it under
  another; for ownership, call `public_share_object` from the test's module. For contention, show
  a shared-object function whose abort blocks a legitimate update.

```move
#[test]
fun field_type_mismatch() {
    dynamic_field::add(&mut uid, 1u64, true);
    // read the same key as a different value type / different key type
    assert!(dynamic_field::exists_<u64, bool>(&uid, 1u64));
}
```

- `sui move build` after adding a `public_share_object` call demonstrates the ownership change.

## Fix

Choose the least-permissive ownership: owned for single-writer resources, `freeze_object` for
constants; avoid `public_share_object`/`public_transfer` on sensitive types. Key dynamic fields with
an unambiguous `(T, K)` and always read with the same pair; use `ObjectTable`/`ObjectBag` when the
value is an object. Use `object::id`/`uid.to_inner()` consistently and `object::delete` on
destruction. Read `ecosystems/move`, `tooling/move-cli`,
`vulnerabilities/move-capability-misuse`.
