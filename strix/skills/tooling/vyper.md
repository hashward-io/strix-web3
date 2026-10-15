---
name: vyper
description: Vyper language and the vyper/titanoboa toolchain — decorators, bounds checks, raw_call/send, fixed-point decimals, and Boa tests for EVM audits
---

# Vyper

Vyper is a Python-flavored, deliberately restricted EVM language; its safety guarantees (no overflow, always bounds-checked) mean bugs cluster around its *escape hatches* and its semantic gaps versus Solidity.

## Install / build

- Compiler: `pipx install vyper` (or `pip install vyper`); check `vyper --version`.
- Test harness: `pip install titanoboa`; `python -c "import boa; print(boa.__version__)"`.
- Compile: `vyper contract.vy` prints bytecode; `vyper -f abi,bytecode,abi_python contract.vy`.
- Artifacts: `vyper -f abi contract.vy > abi.json`; `vyper -f bytecode contract.vy > out.bin`.
- Generate an interface file: `vyper -f interface contract.vy > IFace.vyi`.
- Foundry consumes Vyper via `foundry.toml` `[vyper]` config, or compile and deploy raw bytecode with `cast`.

## Language and semantics vs Solidity

- **Functions:** `def name(arg: type) -> ret:` with decorators `@external`, `@internal`, `@view`, `@pure`, `@payable`, `@deploy` (constructor `__init__`), `@nonreentrant("lock")`.
- **No** inheritance, modifiers, function overloading, recursion, or unbounded loops. Composition is via `interface`/`self`.
- **Visibility:** there is no `public`; `@external` is the ABI surface, `@internal` is callable only via `self.`.
- **Storage:** module-level `owner: public(address)`; `public(...)` auto-generates a getter. `immutable(x: uint256)` and `constant` are compile-time.
- **Bounds checks:** array indexing and slice reads revert when out of range; memory is safe by construction.
- **Overflow:** `uint256`/`int256` arithmetic reverts on overflow and underflow (0.3.x+). `unsafe_add`/`unsafe_sub`/`unsafe_mul`/`unsafe_div` wrap and skip the check — every `unsafe_*` is a lead.
- **Fixed-point:** `decimal` is 10-decimal fixed point; literals like `1.0`; `convert(x, decimal)`; there is no implicit `uint256`↔`decimal` mixing.
- **External calls:** `raw_call(target, data, max_outsize=32, value=0, gas=..., is_delegate_call=False, revert_on_failure=True)` — with `revert_on_failure=False` a failed call returns empty `bytes` (silent-failure lead). `send(to, value) -> bool`. `staticcall(...)`.
- **Reentrancy:** `@nonreentrant` uses a named storage lock; a function without it is fair game, and different keys are independent locks.
- **Assertions:** `assert cond, "msg"`, `raise "msg"`, `raise CustomError`.

## Core commands

```bash
vyper contract.vy
vyper -f abi,bytecode,asm,source_map,metadata contract.vy
vyper -f abi contract.vy > abi.json
vyper -f interface contract.vy > IFace.vyi
vyper --version
```

```python
import boa

src = """
owner: public(address)
@deploy
def __init__():
    self.owner = msg.sender
@external
def set(x: uint256):
    assert msg.sender == self.owner
"""
c = boa.loads(src)
boa.env.eoa = "0x000000000000000000000000000000000000dead"
with boa.reverts("ownable: caller is not the owner"):
    c.set(1, sender=boa.env.generate_address())
```

## Audit workflow

1. `vyper -f abi,bytecode contract.vy` → confirm it compiles; note the pragma `#@version`.
2. Enumerate `@external`/`@payable` functions and which call `self.` (internal) vs foreign targets.
3. Flag every `unsafe_*` arithmetic and every `raw_call(..., revert_on_failure=False)` / unused `send` return — see `vulnerabilities/unchecked-returns`.
4. Check `@nonreentrant` coverage against every external-call path (see `vulnerabilities/reentrancy`).
5. Reproduce High/Critical with a Titanoboa test or a Foundry PoC (`custom/foundry-poc`).

## Pitfalls

- `@nonreentrant` does not protect internal-only paths unless they are called under the lock; additive locks differ per key.
- `send()` returning `False` is ignored if the return value is not checked — funds silently stay.
- Vyper's guarantees only cover what the language models; manual assembly, `raw_call` data, and `create_from_blueprint` re-open Solidity-style risks.
- Version pragmas matter: pre-0.3.4 range checks and pre-0.3.0 arithmetic behave differently.
- See `tooling/solidity` for the shared EVM footguns (delegatecall, `tx.origin`, encodings).
