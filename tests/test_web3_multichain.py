"""Multi-chain target detection and knowledge-layer tests for Strix Web3.

Covers the expanded ``infer_target_type`` (EVM plus Solana, Move, Cairo,
CosmWasm, TON, and Bitcoin address shapes) and the new skill categories
(``ecosystems/`` and ``reference/``) that give the engine non-EVM support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from strix.interface.utils import infer_target_type
from strix.skills import get_available_skills, load_skills


if TYPE_CHECKING:
    from pathlib import Path


_EVM_ADDRESS = "0x0123456789abcdef0123456789abcdef01234567"
_SOLANA_ADDRESS = "9xQeWvG816bUx9EPfNqNKpS4Zk5N7gVvDLJq7YvYhq3f"
_STARKNET_ADDRESS = "0x" + "ab" * 32
_SUI_PACKAGE = "0x" + "cd" * 32
_COSMOS_ADDRESS = "cosmos1qypqxpq9qcrsszg2pvxq6rs0zqg3yyc5lzv7xu"
_TON_FRIENDLY = "EQ" + "a" * 46
_TON_RAW = "0:" + "ef" * 32
_BITCOIN_ADDRESS = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"


@pytest.mark.parametrize(
    ("target", "expected_ecosystem"),
    [
        (_EVM_ADDRESS, "evm"),
        (_SOLANA_ADDRESS, "solana"),
        (_STARKNET_ADDRESS, ""),
        (_SUI_PACKAGE, ""),
        (_COSMOS_ADDRESS, "cosmwasm"),
        (_TON_FRIENDLY, "ton"),
        (_TON_RAW, "ton"),
        (_BITCOIN_ADDRESS, "bitcoin"),
    ],
)
def test_bare_address_detects_ecosystem(target: str, expected_ecosystem: str) -> None:
    target_type, details = infer_target_type(target)

    assert target_type == "deployed_contract"
    assert details["target_address"] == target
    assert details.get("ecosystem", "") == expected_ecosystem


@pytest.mark.parametrize(
    ("target", "expected_chain", "expected_ecosystem"),
    [
        (f"1:{_EVM_ADDRESS}", "1", "evm"),
        (f"mainnet:{_EVM_ADDRESS}", "mainnet", "evm"),
        (f"solana:{_SOLANA_ADDRESS}", "solana", "solana"),
        (f"starknet:{_STARKNET_ADDRESS}", "starknet", "cairo"),
        (f"sui:{_SUI_PACKAGE}", "sui", "move"),
        (f"aptos:{_SUI_PACKAGE}", "aptos", "move"),
        (f"cosmos:{_COSMOS_ADDRESS}", "cosmos", "cosmwasm"),
        (f"ton:{_TON_FRIENDLY}", "ton", "ton"),
        (f"bitcoin:{_BITCOIN_ADDRESS}", "bitcoin", "bitcoin"),
    ],
)
def test_chain_qualified_addresses(
    target: str, expected_chain: str, expected_ecosystem: str
) -> None:
    target_type, details = infer_target_type(target)

    assert target_type == "deployed_contract"
    assert details["chain"] == expected_chain
    assert details["ecosystem"] == expected_ecosystem


def test_sui_short_form_package_id_with_chain() -> None:
    """Sui/Aptos allow short-form hex ids, but only with a chain token."""
    target_type, details = infer_target_type("sui:0x2")

    assert target_type == "deployed_contract"
    assert details["target_address"] == "0x2"
    assert details["ecosystem"] == "move"


def test_short_form_hex_without_known_chain_is_not_an_address() -> None:
    with pytest.raises(ValueError):
        infer_target_type("notachain:0x2")


@pytest.mark.parametrize(
    "target",
    [
        "git@github.com:org/protocol.git",
        "git://github.com/org/protocol.git",
    ],
)
def test_git_urls_are_not_mistaken_for_addresses(target: str) -> None:
    target_type, details = infer_target_type(target)

    assert target_type == "repository"
    assert details["target_repo"] == target


def test_local_directory_is_local_code(tmp_path: Path) -> None:
    target_type, details = infer_target_type(str(tmp_path))

    assert target_type == "local_code"
    assert details["target_path"] == str(tmp_path.resolve())


def test_skill_categories_include_ecosystems_and_reference() -> None:
    available = get_available_skills()

    assert "evm" in {s["name"] for s in available["ecosystems"]}
    assert "solana" in {s["name"] for s in available["ecosystems"]}
    assert "scsvs-checklist" in {s["name"] for s in available["reference"]}
    # Non-EVM bug classes are user-selectable.
    vuln_names = {s["name"] for s in available["vulnerabilities"]}
    assert {
        "solana-cpi-safety",
        "move-capability-misuse",
        "zk-underconstrained-circuit",
    } <= vuln_names


def test_non_evm_skills_load() -> None:
    names = [
        "ecosystems/solana",
        "ecosystems/move",
        "vulnerabilities/solana-cpi-safety",
        "vulnerabilities/cairo-felt-and-math",
        "tooling/move-cli",
        "tooling/zk-circom",
        "reference/scsvs-checklist",
        "reconnaissance/ecosystem-detection",
    ]
    loaded = load_skills(names)

    for name in names:
        assert loaded.get(name.split("/")[-1]), f"{name} failed to load"


def test_internal_categories_are_not_user_selectable() -> None:
    available = get_available_skills()

    assert "analysis" not in available
    assert "coordination" not in available
    assert "scan_modes" not in available
