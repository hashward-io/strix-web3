---
name: ton
description: TON toolchain — FunC/Tact compilers, Blueprint build/test, @ton/sandbox, ton-cli/fift, tact.config.json, and computePhase gas analysis
---

# TON (FunC / Tact)

TON contracts are FunC (low-level, assembled to Fift) or Tact (high-level) compiled to TVM bytecode; calls arrive as internal or external messages and gas is metered by the `computePhase`.

## Install / build

- Tact compiler: `npm install -g @tact-lang/compiler`; `tact --version`.
- FunC: `func` from the TON repo or via `ton-compiler`; `func -h`.
- Blueprint (dev framework): `npm create ton@latest` and choose Blueprint; `npx blueprint --version`.
- Tools: `fift` (Fift interpreter), `ton-cli` (`npm install -g ton-cli`), `@ton/sandbox` (`npm install @ton/sandbox`).
- Testnet faucet: the TON testnet faucet bot or `blueprint` testnet deploy.

## tact.config.json

```json
{
  "projects": [
    {
      "name": "my_contract",
      "path": "./contracts/my_contract.tact",
      "output": "./build",
      "options": { "debug": true }
    }
  ]
}
```

## Core commands

```bash
# FunC
func -SPA -o build/main.fif contracts/main.fc
fift -s build/main.fif

# Tact
tact -c tact.config.json
tact --check contracts/my_contract.tact

# Blueprint
npx blueprint create MyProject
npx blueprint build
npx blueprint test
npx blueprint run deployMyProject --testnet --tonconnect

# network
npx blueprint run --custom <script>
ton-cli --version
```

## @ton/sandbox test

```typescript
import { Blockchain } from "@ton/sandbox";
const blockchain = await Blockchain.create();
const result = await contract.sendDeploy(deployer.getSender(), toNano("0.05"));
result.transactions.forEach(tx => console.log(tx.description.computePhase));
```

## Audit workflow

1. `npx blueprint build` → green, then `npx blueprint test` for the baseline.
2. Read the `.tact`/`.fc` source for `receive`/`recv` handlers and get-methods.
3. Check sender handling: internal vs external messages, `sender_address()` vs `sender()`, and bounce flags — see `ecosystems/ton`.
4. Inspect jetton `transfer_notification` trust and cell-depth/serialization bounds.
5. Watch `computePhase` for gas bombs (cell depth, unbounded dict/boc loads).
6. Confirm High/Critical with a Blueprint sandbox test asserting balances and exit codes.

## Pitfalls

- Get-methods are off-chain and not consensus; never rely on them for on-chain state.
- External messages have no sender; authenticating on `sender_address()` inside an external handler is forgeable.
- Bounced messages must be handled; ignoring the bounce flag can strand funds.
- Tact's automatic message parsing can mis-type a malformed cell — validate fields before trusting them.
- `fift`/`func` are low-level and version-sensitive; pin the toolchain used for a build.
