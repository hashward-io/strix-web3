"""On-chain target recognition — one source of truth for address shapes.

Both the interface layer (to route a target to a scan) and the audit tools (to
key a threat model by target) need to answer "is this string a deployed
contract, and which ecosystem is it?". Keeping the patterns and the parser here
stops the two layers drifting apart; this module imports nothing but ``re`` so
either layer can depend on it cheaply.
"""

from __future__ import annotations

import re
from urllib.parse import unquote


# Address shapes by ecosystem. An ecosystem of "" means "a chain address whose
# chain we could not infer"; the agent resolves the chain itself.
EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
WIDE_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")  # Move/Aptos/Sui/Starknet: 32-byte id
# Sui/Aptos allow short-form hex ids (e.g. ``0x2``); only accepted with a chain token.
SHORT_HEX_RE = re.compile(r"^0x[0-9a-fA-F]{1,63}$")
SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
TON_FRIENDLY_RE = re.compile(r"^(?:EQ|UQ|kQ|0Q)[A-Za-z0-9_-]{46}$")
TON_RAW_RE = re.compile(r"^-?\d+:[0-9a-fA-F]{64}$")
COSMOS_ADDRESS_RE = re.compile(r"^[a-z][a-z0-9]{2,15}1[023456789acdefghjklmnpqrstuvwxyz]{11,}$")
BITCOIN_ADDRESS_RE = re.compile(r"^(?:bc1|tb1|bcrt1)[023456789acdefghjklmnpqrstuvwxyz]{11,}$")
CARDANO_ADDRESS_RE = re.compile(r"^(?:addr1|addr_test1|stake1|stake_test1)[0-9a-z]{20,}$")
ALGORAND_ADDRESS_RE = re.compile(r"^[A-Z2-7]{58}$")

#: Chain/ecosystem tokens we recognize in a ``<chain>:<address>`` spelling.
CHAIN_ECOSYSTEMS: dict[str, str] = {
    # EVM
    "eth": "evm",
    "ethereum": "evm",
    "mainnet": "evm",
    "evm": "evm",
    "arbitrum": "evm",
    "optimism": "evm",
    "base": "evm",
    "polygon": "evm",
    "bsc": "evm",
    "avalanche": "evm",
    "avax": "evm",
    "linea": "evm",
    "scroll": "evm",
    "zksync": "evm",
    "blast": "evm",
    "celo": "evm",
    # Non-EVM
    "sol": "solana",
    "solana": "solana",
    "sui": "move",
    "aptos": "move",
    "move": "move",
    "starknet": "cairo",
    "cairo": "cairo",
    "stark": "cairo",
    "cosmos": "cosmwasm",
    "cosmwasm": "cosmwasm",
    "osmosis": "cosmwasm",
    "osmo": "cosmwasm",
    "neutron": "cosmwasm",
    "sei": "cosmwasm",
    "ton": "ton",
    "toncoin": "ton",
    "polkadot": "substrate",
    "substrate": "substrate",
    "ink": "substrate",
    "kusama": "substrate",
    "fuel": "sway",
    "sway": "sway",
    "near": "near",
    "bitcoin": "bitcoin",
    "btc": "bitcoin",
    "circom": "zk",
    "noir": "zk",
    "zk": "zk",
    "algorand": "algorand",
    "algo": "algorand",
    "avm": "algorand",
    "cardano": "cardano",
    "ada": "cardano",
    "aiken": "cardano",
    "plutus": "cardano",
}

#: Address regex → ecosystem, checked in order. Excludes the shared 32-byte hex
#: and short-form hex shapes, which need the chain token to disambiguate.
#: Specific bech32 HRPs (Bitcoin, Cardano) precede the generic Cosmos pattern.
ADDRESS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (EVM_ADDRESS_RE, "evm"),
    (TON_FRIENDLY_RE, "ton"),
    (TON_RAW_RE, "ton"),
    (SOLANA_ADDRESS_RE, "solana"),
    (BITCOIN_ADDRESS_RE, "bitcoin"),
    (CARDANO_ADDRESS_RE, "cardano"),
    (ALGORAND_ADDRESS_RE, "algorand"),
    (COSMOS_ADDRESS_RE, "cosmwasm"),
)


def ecosystem_from_chain(token: str) -> str:
    """Map a chain token (``eth``, ``solana``, ``sui`` …) to its ecosystem."""
    return CHAIN_ECOSYSTEMS.get(token.strip().lower(), "")


def looks_like_address(candidate: str) -> bool:
    """Whether ``candidate`` has the shape of an address in any ecosystem."""
    return any(
        pattern.match(candidate)
        for pattern in (
            EVM_ADDRESS_RE,
            WIDE_ADDRESS_RE,
            SHORT_HEX_RE,
            SOLANA_ADDRESS_RE,
            TON_FRIENDLY_RE,
            TON_RAW_RE,
            COSMOS_ADDRESS_RE,
            BITCOIN_ADDRESS_RE,
            CARDANO_ADDRESS_RE,
            ALGORAND_ADDRESS_RE,
        )
    )


def ecosystem_for_address(address: str, chain: str) -> str | None:
    """Return the ecosystem for an address, ``""`` when it is an address of an
    unknown chain, or ``None`` when it is not an on-chain address at all."""
    for pattern, ecosystem in ADDRESS_PATTERNS:
        if pattern.match(address):
            return ecosystem
    if WIDE_ADDRESS_RE.match(address):
        # 32-byte ids are shared by Move (Sui/Aptos) and Starknet; the chain token
        # disambiguates, otherwise the agent resolves it from context.
        return ecosystem_from_chain(chain) or ""
    if SHORT_HEX_RE.match(address):
        # Short-form hex is only meaningful when the chain token names the chain.
        return ecosystem_from_chain(chain) or None
    return None


def parse_deployed_contract_target(target: str) -> dict[str, str] | None:
    """Recognize a deployed on-chain target in any supported ecosystem.

    Accepted spellings:

    - An address alone: EVM ``0x<40 hex>``, Solana base58, Sui/Aptos/Starknet
      ``0x<64 hex>``, Cosmos bech32 (``cosmos1...``), Cardano bech32
      (``addr1...``/``stake1...``), Algorand base32, TON friendly/raw, or a
      Bitcoin ``bc1...`` address.
    - ``<chain>:<address>`` — pin the chain, e.g. ``1:0x...``, ``solana:<base58>``,
      ``sui:0x<64 hex>``, ``starknet:0x...``. The chain token is stored verbatim
      and passed to the agent, which resolves it against its RPC configuration.
    """
    candidate = target.strip()

    if TON_RAW_RE.match(candidate):
        return {"target_address": candidate, "ecosystem": "ton"}

    chain = ""
    address = candidate
    if ":" in candidate and not candidate.startswith("0x"):
        chain_token, _, remainder = candidate.partition(":")
        remainder = remainder.strip()
        if chain_token.strip() and looks_like_address(remainder):
            chain = chain_token.strip()
            address = remainder

    ecosystem = ecosystem_for_address(address, chain)
    if ecosystem is None:
        return None

    details: dict[str, str] = {"target_address": address}
    if chain:
        details["chain"] = chain
    if ecosystem:
        details["ecosystem"] = ecosystem
    return details


def address_from_url(url_path: str) -> dict[str, str] | None:
    """Recover an on-chain address from a block-explorer URL path.

    Explorers put the address in the path (``/address/0x…``, ``/account/<addr>``,
    ``/token/0x…``). Web3 users paste these links, so return deployed-contract
    details when a path segment is an unambiguous address. A bare 32-byte hex id
    is rejected: it is as likely a transaction hash as a Move/Starknet contract,
    so it is only accepted with a ``<chain>:<address>`` token.
    """
    for segment in reversed([part for part in url_path.split("/") if part]):
        candidate = unquote(segment)
        parsed = parse_deployed_contract_target(candidate)
        if parsed is None:
            continue
        if not parsed.get("ecosystem") and WIDE_ADDRESS_RE.match(parsed.get("target_address", "")):
            continue
        return parsed
    return None


def on_chain_identity(target: str) -> str | None:
    """A stable key for a deployed contract, or ``None`` if not one.

    Addresses are case-insensitive when hex (EVM, Sui/Aptos/Starknet ids, TON
    raw) and case-sensitive otherwise (base58, bech32), so only the hex forms
    are lowercased. The chain token, when present, is lowercased and kept, so
    ``eth:0xAB…`` and ``0xab…`` remain distinct keys while ``EVM:0xab…`` and
    ``evm:0xab…`` converge.
    """
    details = parse_deployed_contract_target(target)
    if details is None:
        return None
    address = details["target_address"]
    if address.startswith("0x") or ":" in address:  # hex, or TON raw ``<wc>:<hex>``
        address = address.lower()
    chain = details.get("chain", "").strip().lower()
    return f"{chain}:{address}" if chain else address


__all__ = [
    "ADDRESS_PATTERNS",
    "CHAIN_ECOSYSTEMS",
    "address_from_url",
    "ecosystem_for_address",
    "ecosystem_from_chain",
    "looks_like_address",
    "on_chain_identity",
    "parse_deployed_contract_target",
]
