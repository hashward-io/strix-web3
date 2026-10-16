"""Target inference: Web3 targets only, and a clear error for anything else.

The engine audits blockchain protocols. A URL, a bare domain, or a bare IP is
not a Web3 target, so inference must reject it instead of silently producing a
``web_application`` target with no playbook. A block-explorer URL that carries a
real address is recovered as a deployed contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from strix.interface import utils
from strix.interface.utils import infer_target_type
from strix.utils.targets import on_chain_identity


if TYPE_CHECKING:
    from pathlib import Path


EVM_ADDRESS = "0x1111111111111111111111111111111111111111"
SOLANA_ADDRESS = "So11111111111111111111111111111111111111112"
SUBSTRATE_ADDRESS = "5C4iA2und8WV6mbvTBYupm2eZwtxk3wCYUM2SFHXSyQuapGp"
SUBSTRATE_ACCOUNT_ID20 = "sKDJwGgP42ifhnUdJMqgNVjwJACq3hg"


def test_evm_address_is_a_deployed_contract() -> None:
    ttype, details = infer_target_type(EVM_ADDRESS)

    assert ttype == "deployed_contract"
    assert details["target_address"] == EVM_ADDRESS
    assert details["ecosystem"] == "evm"


@pytest.mark.parametrize(
    ("target", "ecosystem"),
    [
        (f"solana:{SOLANA_ADDRESS}", "solana"),
        ("ton:0:1111111111111111111111111111111111111111111111111111111111111111", "ton"),
        ("starknet:0x1111111111111111111111111111111111111111111111111111111111111111", "cairo"),
        ("sui:0x2", "move"),
        ("bitcoin:bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", "bitcoin"),
        ("cardano:addr1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "cardano"),
        ("near:contract.near", "near"),
        ("near:contract", "near"),
        ("polkadot:" + SUBSTRATE_ADDRESS, "substrate"),
        ("fuel:fuel1" + "q" * 55, "sway"),
    ],
)
def test_chain_pinned_addresses_resolve_their_ecosystem(target: str, ecosystem: str) -> None:
    ttype, details = infer_target_type(target)

    assert ttype == "deployed_contract"
    assert details["ecosystem"] == ecosystem
    assert details["chain"] == target.split(":", 1)[0]


def test_explorer_url_recovers_the_address() -> None:
    ttype, details = infer_target_type(f"https://etherscan.io/address/{EVM_ADDRESS}")

    assert ttype == "deployed_contract"
    assert details["target_address"] == EVM_ADDRESS


def test_bare_near_account_id_is_a_deployed_target() -> None:
    ttype, details = infer_target_type("contract.near")

    assert ttype == "deployed_contract"
    assert details["target_address"] == "contract.near"
    assert details["ecosystem"] == "near"


@pytest.mark.parametrize(
    ("target", "ecosystem"),
    [
        (SUBSTRATE_ADDRESS, "substrate"),
        (SUBSTRATE_ACCOUNT_ID20, "substrate"),
        ("fuel1" + "q" * 55, "sway"),
    ],
)
def test_bare_substrate_and_fuel_addresses_are_inferred(target: str, ecosystem: str) -> None:
    ttype, details = infer_target_type(target)

    assert ttype == "deployed_contract"
    assert details["ecosystem"] == ecosystem


def test_explorer_url_with_query_still_recovers_the_address() -> None:
    ttype, details = infer_target_type(
        f"https://solscan.io/account/{SOLANA_ADDRESS}?cluster=mainnet"
    )

    assert ttype == "deployed_contract"
    assert details["ecosystem"] == "solana"


def test_explorer_tx_url_is_not_treated_as_a_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A 64-hex transaction hash in the path must not become a contract target.
    monkeypatch.setattr(utils, "_is_http_git_repo", lambda _url: False)
    with pytest.raises(ValueError, match="web URL"):
        infer_target_type(f"https://etherscan.io/tx/0x{'a' * 64}")


@pytest.mark.parametrize(
    "target",
    [
        "https://example.com",
        "https://app.example.com/dashboard",
        "example.com",
        "1.2.3.4",
        "postman://abc-123",
    ],
)
def test_non_web3_targets_are_rejected(target: str) -> None:
    with pytest.raises(ValueError):
        infer_target_type(target)


def test_local_directory_is_a_codebase(tmp_path: Path) -> None:
    project = tmp_path / "protocol"
    project.mkdir()

    ttype, details = infer_target_type(str(project))

    assert ttype == "local_code"
    assert details["target_path"] == str(project.resolve())


def test_single_file_is_not_a_target(tmp_path: Path) -> None:
    spec = tmp_path / "abi.json"
    spec.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="not a directory"):
        infer_target_type(str(spec))


def test_scp_style_git_remote_is_a_repository() -> None:
    ttype, details = infer_target_type("git@github.com:acme/protocol.git")

    assert ttype == "repository"
    assert details["target_repo"] == "git@github.com:acme/protocol.git"


def test_git_suffix_url_is_a_repository() -> None:
    ttype, details = infer_target_type("https://github.com/acme/protocol.git")

    assert ttype == "repository"
    assert details["target_repo"].endswith(".git")


def test_on_chain_identity_folds_hex_and_chain_case() -> None:
    # The shared module is what the threat-model store keys targets on, so a
    # hex address and its chain token must normalize to one identity.
    assert on_chain_identity("EVM:0x" + "AB" * 20) == "evm:0x" + "ab" * 20
    assert on_chain_identity("0x" + "AB" * 20) == "0x" + "ab" * 20


def test_on_chain_identity_preserves_base58_case() -> None:
    # Base58 is case-sensitive: the two spellings are different contracts.
    assert on_chain_identity(SOLANA_ADDRESS) == SOLANA_ADDRESS
    assert on_chain_identity(SOLANA_ADDRESS.lower()) != on_chain_identity(SOLANA_ADDRESS)


def test_on_chain_identity_is_none_for_non_targets() -> None:
    assert on_chain_identity("https://github.com/acme/protocol") is None
    assert on_chain_identity("/workspace/protocol") is None
    assert on_chain_identity("foo:bar") is None
