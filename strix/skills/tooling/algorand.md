---
name: algorand
description: Algorand toolchain - algokit init/localnet/compile/deploy, goal, AlgoKit Utils pytest harness, ARC-4/ARC-56 app spec, localnet debugging
---

# Algorand (AlgoKit / AVM)

AlgoKit is the canonical Algorand development toolchain: it scaffolds projects, runs a Docker **localnet** (algod + kmd + indexer), compiles Algorand Python / PyTeal, and deploys. `goal` talks to the node directly; `algokit-utils` drives integration tests.

## Install / build

- Install AlgoKit: `curl -fsSL https://cli.algokit.io/install.sh | bash`, or `uv tool install algokit`; verify with `algokit --version` and `algokit doctor`.
- Docker (Compose v2.5.0+) must be running for `algokit localnet`. The Strix sandbox has **no Docker daemon**, so in-sandbox prefer pure-Python unit tests against a remote/local node, or an `algokit-utils` test that the user runs where Docker is available.
- Python 3.12+ for PuyaPy; deps live in `pyproject.toml` (Poetry/uv). `algokit project bootstrap all` installs and builds.
- The PuyaPy compiler may be project-local or resolved dynamically; pin its version for reproducible bytecode.

## Core commands

```bash
# scaffold / bootstrap
algokit init                                          # pick a template (python, pyteal, ...)
algokit project bootstrap all                         # install deps + build artifacts
algokit generate client app.arc56.json --output-dir ./client

# localnet (Docker: algod + kmd + indexer)
algokit localnet start
algokit localnet status
algokit localnet reset                                # wipe all local state
algokit localnet stop

# compile (PuyaPy)
algokit compile python smart_contracts/contract.py --out-dir out
algokit compile py smart_contracts                    # alias for 'compile python'

# deploy
algokit deploy                                        # runs deploy_config.py
algokit project deploy localnet

# goal (node / account / app)
algokit goal node status
algokit goal account list
algokit goal account balance --address <ADDR>
algokit goal app call --app-id <ID> --from <ADDR> --app-arg "str:hello"
algokit goal app read --app-id <ID> --global
algokit goal app box read --app-id <ID> --name "str:mybox"
algokit goal clerk send --from <A> --to <B> --amount 1000000
algokit goal group create ...                         # assemble an atomic group
```

## algokit-utils test harness

```python
from algokit_utils import AlgorandClient, AlgoAmount

algorand = AlgorandClient.default_localnet()          # or from_environment()
algorand.set_default_signer(algorand.account.random())
factory = algorand.client.get_typed_app_factory(MyContractFactory)
app_client, _ = factory.send.create.create()
app_client.send.my_method(arg=1)
print(app_client.state.global_state.get_all())
```

- `AlgorandClient` (`from_environment`, `default_localnet`, `testnet`, `mainnet`) wraps algod, kmd, and indexer.
- Typed app clients (`get_typed_app_client`) and the generic `ApplicationClient` call methods by ARC-4 selector and expose `.state` for global/local/box reads.
- `algorand.new_group()` / `TransactionComposer` builds multi-txn **atomic groups**, including inner-call groups.
- AVM unit tests (`algorand-python-testing`) cover single-program logic without a node.

## Audit workflow

1. `algokit project bootstrap all` and `algokit localnet start`; run `pytest` for a green baseline.
2. Read the ARC-56 app spec (`application.json` / `.arc56.json`) to enumerate methods, args, and state schema.
3. List `@arc4.abimethod` (ABI, selector-routed) vs bare `@arc4.baremethod` entry points and their `on_completion`.
4. Grep the AVM surfaces: `Gtxn`, `itxn`, `Txn.group_index`, `Txn.fee`, `Txn.sender`, `Txn.rekey_to`, `Txn.close_remainder_to`, `asset_sender`, `Box`, `App.globalGetEx`.
5. Trace every group and inner-txn assumption against `vulnerabilities/algorand-group-transactions`, `vulnerabilities/algorand-account-and-rekey`, `vulnerabilities/algorand-inner-and-storage`.
6. Confirm High/Critical with a localnet `pytest` asserting balances, state, and boxes.

## Pitfalls

- `algokit localnet` needs Docker; a stopped engine makes tests error rather than fail.
- The PuyaPy/`algopy` version must match the lockfile or bytecode drifts; recompile before testing.
- ARC-4 selectors are the first 4 bytes of SHA-512/256 of the method signature — a renamed method changes routing silently.
- Localnet block timing differs from mainnet; `Global.round`/timing assumptions can pass locally and fail on-chain.
- `goal app read` shows global/local state but not boxes — use `goal app box read` or `app_client.state`.
- Fee pooling and opcode-budget pooling behave the same on localnet as mainnet but are easy to under-test; always submit the whole group, not one txn.
