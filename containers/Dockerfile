# ---------------------------------------------------------------------------
# Strix Web3 — multi-ecosystem smart-contract audit sandbox
#
# Ecosystem toolchains installed:
#   EVM          forge/cast/anvil, slither, aderyn, echidna, medusa, halmos,
#                solc, vyper/boa, hardhat, cargo-stylus (Arbitrum)
#   Solana       solana-cli, anchor (avm), solana-test-validator, spl-token
#   Move         sui, aptos, move prover
#   Cairo        scarb, snforge/sncast (starknet-foundry), cairo-lint
#   CosmWasm     wasm32 target, cosmwasm-check, cw-multitest (crate)
#   ZK           circom, snarkjs, circomspect, nargo (Noir)
#   TON          func, tact, blueprint
#   Substrate    cargo-contract (ink!)
#   Sway/Fuel    forc, fuel-core (fuelup)
#   NEAR         cargo-near
#   Algorand     algokit (AlgoKit CLI), algokit-utils (Python test harness)
#   Cardano      aiken (via aikup), plutus tooling
#   Bitcoin      bitcoin-cli/bitcoind (regtest), rust-miniscript (crate)
#
# Build the full multi-chain image:
#   docker build -f containers/Dockerfile -t strix-sandbox:dev .
# EVM-only, faster build:
#   docker build --build-arg INSTALL_EXTRA_CHAINS=0 -f containers/Dockerfile -t strix-sandbox:dev .
# ---------------------------------------------------------------------------
FROM debian:bookworm-slim

ARG TARGETARCH
ARG INSTALL_EXTRA_CHAINS=1

LABEL description="Strix Web3 sandbox — multi-ecosystem smart-contract audit toolchain"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl wget git jq unzip tar xz-utils \
        build-essential pkg-config cmake clang libssl-dev \
        python3 python3-venv python3-pip pipx \
        nodejs npm \
        sudo less file xxd ripgrep procps \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash auditor && \
    usermod -aG sudo auditor && \
    echo "auditor ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    touch /home/auditor/.hushlogin

USER auditor
WORKDIR /tmp

# uv for Python tooling.
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/home/auditor/.local/bin sh

# ---------------------------------------------------------------------------
# Rust toolchain — the base for Solana/CosmWasm/ink!/NEAR/Circom/Stylus tooling.
# ---------------------------------------------------------------------------
ENV CARGO_HOME="/home/auditor/.cargo"
ENV RUSTUP_HOME="/home/auditor/.rustup"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --default-toolchain stable --profile minimal && \
    /home/auditor/.cargo/bin/rustup target add wasm32-unknown-unknown && \
    /home/auditor/.cargo/bin/rustc --version

# ---------------------------------------------------------------------------
# EVM: Foundry, solc, Slither/Halmos, static analyzers, fuzzers.
# ---------------------------------------------------------------------------
ENV PATH="/home/auditor/.foundry/bin:/home/auditor/.aiken/bin:/home/auditor/.local/bin:${PATH}"
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /home/auditor/.foundry/bin/foundryup && \
    /home/auditor/.foundry/bin/forge --version

RUN python3 -m venv /home/auditor/.venv && \
    /home/auditor/.venv/bin/pip install --no-cache-dir --upgrade pip wheel && \
    /home/auditor/.venv/bin/pip install --no-cache-dir \
        slither-analyzer crytic-compile \
        halmos \
        vyper titanoboa \
        web3 eth-abi eth-utils py-solc-x \
        algokit-utils \
        requests && \
    /home/auditor/.venv/bin/slither --version

# Aderyn (Rust static analyzer).
RUN set -eux; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) ADERYN_ARCH="x86_64" ;; \
        arm64) ADERYN_ARCH="aarch64" ;; \
        *) echo "Unsupported arch for aderyn" >&2; exit 1 ;; \
    esac; \
    TAG="$(curl -fsSL https://api.github.com/repos/Cyfrin/aderyn/releases/latest | jq -r .tag_name)"; \
    curl -fsSL "https://github.com/Cyfrin/aderyn/releases/download/${TAG}/aderyn-${ADERYN_ARCH}-unknown-linux-gnu.tar.xz" -o /tmp/aderyn.txz; \
    tar -xJf /tmp/aderyn.txz -C /tmp; \
    mkdir -p /home/auditor/.local/bin; \
    install -m 0755 "/tmp/aderyn-${ADERYN_ARCH}-unknown-linux-gnu/aderyn" /home/auditor/.local/bin/aderyn; \
    rm -rf "/tmp/aderyn-${ADERYN_ARCH}-unknown-linux-gnu" /tmp/aderyn.txz; \
    /home/auditor/.local/bin/aderyn --version

# Echidna (property-based fuzzer).
RUN set -eux; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) ECHIDNA_ARCH="x86_64" ;; \
        arm64) ECHIDNA_ARCH="aarch64" ;; \
        *) echo "Unsupported arch for echidna" >&2; exit 1 ;; \
    esac; \
    TAG="$(curl -fsSL https://api.github.com/repos/crytic/echidna/releases/latest | jq -r .tag_name)"; \
    VER="${TAG#v}"; \
    curl -fsSL "https://github.com/crytic/echidna/releases/download/${TAG}/echidna-${VER}-${ECHIDNA_ARCH}-linux.tar.gz" -o /tmp/echidna.tgz; \
    tar -xzf /tmp/echidna.tgz -C /tmp; \
    install -m 0755 /tmp/echidna /home/auditor/.local/bin/echidna; \
    rm -f /tmp/echidna /tmp/echidna.tgz; \
    /home/auditor/.local/bin/echidna --version || true

# Medusa (coverage-guided stateful fuzzer). Upstream ships linux/amd64 (x64) only.
RUN set -eux; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) MEDUSA_ARCH="x64" ;; \
        arm64) echo "medusa: no linux/arm64 release; skipping" >&2; MEDUSA_ARCH="" ;; \
        *) echo "Unsupported arch for medusa" >&2; exit 1 ;; \
    esac; \
    if [ -n "${MEDUSA_ARCH}" ]; then \
        TAG="$(curl -fsSL https://api.github.com/repos/crytic/medusa/releases/latest | jq -r .tag_name)"; \
        curl -fsSL "https://github.com/crytic/medusa/releases/download/${TAG}/medusa-linux-${MEDUSA_ARCH}.tar.gz" -o /tmp/medusa.tgz; \
        tar -xzf /tmp/medusa.tgz -C /tmp; \
        find /tmp -maxdepth 3 -type f -name 'medusa' -exec install -m 0755 {} /home/auditor/.local/bin/medusa \; ; \
        rm -rf /tmp/medusa /tmp/medusa.tgz; \
        /home/auditor/.local/bin/medusa --version || true; \
    fi

# ---------------------------------------------------------------------------
# Ecosystem toolchains. Gate off with INSTALL_EXTRA_CHAINS=0. One layer per
# ecosystem so a single broken download only rebuilds that ecosystem (and so
# CI/user builds still cache the ecosystems that do work).
# ---------------------------------------------------------------------------

# --- Solana ----------------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    export PATH="/home/auditor/.cargo/bin:${PATH}"; \
    sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"; \
    /home/auditor/.local/share/solana/install/active_release/bin/solana --version; \
    cargo install --git https://github.com/coral-xyz/anchor avm --locked --force; \
    /home/auditor/.cargo/bin/avm install latest; \
    /home/auditor/.cargo/bin/avm use latest; \
    fi

# --- Move: Sui + Aptos -----------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    curl -fsSL "https://aptos.dev/scripts/install_cli.py" | python3; \
    SUI_TAG="$(curl -fsSL https://api.github.com/repos/MystenLabs/sui/releases/latest | jq -r .tag_name)"; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) SUI_ARCH="ubuntu-x86_64" ;; \
        arm64) SUI_ARCH="ubuntu-aarch64" ;; \
        *) echo "Unsupported arch for sui" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://github.com/MystenLabs/sui/releases/download/${SUI_TAG}/sui-${SUI_TAG}-${SUI_ARCH}.tgz" -o /tmp/sui.tgz; \
    tar -xzf /tmp/sui.tgz -C /home/auditor/.local/bin; \
    rm -f /tmp/sui.tgz; \
    fi

# --- Cairo / Starknet ------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    export PATH="/home/auditor/.cargo/bin:${PATH}"; \
    curl --proto '=https' --tlsv1.2 -sSf https://docs.swmansion.com/scarb/install.sh | sh -s --; \
    /home/auditor/.local/bin/scarb --version; \
    curl -L https://raw.githubusercontent.com/foundry-rs/starknet-foundry/master/scripts/install.sh | sh; \
    /home/auditor/.local/bin/snfoundryup || true; \
    fi

# --- CosmWasm --------------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    export PATH="/home/auditor/.cargo/bin:${PATH}"; \
    cargo install --locked cosmwasm-check; \
    fi

# --- ZK: Circom, circomspect, Noir -----------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    export PATH="/home/auditor/.cargo/bin:${PATH}"; \
    export SHELL=/bin/bash; \
    export NPM_CONFIG_PREFIX=/home/auditor/.local; \
    cargo install --git https://github.com/iden3/circom.git --locked --force circom; \
    cargo install circomspect --locked; \
    curl -L https://raw.githubusercontent.com/noir-lang/noirup/main/install | bash; \
    /home/auditor/.nargo/bin/noirup || true; \
    npm install -g snarkjs; \
    fi

# --- TON -------------------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    export NPM_CONFIG_PREFIX=/home/auditor/.local; \
    npm install -g @tact-lang/compiler @ton/blueprint; \
    fi

# --- Substrate / ink! ------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    export PATH="/home/auditor/.cargo/bin:${PATH}"; \
    cargo install --locked cargo-contract; \
    fi

# --- Sway / Fuel -----------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    curl https://install.fuel.network | sh -s -- --no-modify-path; \
    fi

# --- NEAR ------------------------------------------------------------------
# cargo-near -> near-cli-rs -> hidapi (Ledger) needs libudev headers.
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    sudo apt-get update; \
    sudo apt-get install -y --no-install-recommends libudev-dev; \
    sudo rm -rf /var/lib/apt/lists/*; \
    export PATH="/home/auditor/.cargo/bin:${PATH}"; \
    cargo install --locked cargo-near; \
    fi

# --- Arbitrum Stylus -------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    export PATH="/home/auditor/.cargo/bin:${PATH}"; \
    cargo install --locked cargo-stylus; \
    fi

# --- Algorand (AVM) --------------------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    pipx install algokit; \
    /home/auditor/.local/bin/algokit --version; \
    fi

# --- Cardano (Aiken / Plutus) ----------------------------------------------
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    curl -sSfL https://install.aiken-lang.org | bash; \
    /home/auditor/.aiken/bin/aikup install; \
    /home/auditor/.aiken/bin/aiken --version; \
    fi

# Bitcoin Core (regtest) for Script/Miniscript testing.
RUN if [ "${INSTALL_EXTRA_CHAINS}" = "1" ]; then set -eux; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) BTC_ARCH="x86_64-linux-gnu" ;; \
        arm64) BTC_ARCH="aarch64-linux-gnu" ;; \
        *) BTC_ARCH="" ;; \
    esac; \
    if [ -n "${BTC_ARCH}" ]; then \
        BTC_VER="27.0"; \
        curl -fsSL "https://bitcoincore.org/bin/bitcoin-core-${BTC_VER}/bitcoin-${BTC_VER}-${BTC_ARCH}.tar.gz" -o /tmp/bitcoin.tgz; \
        tar -xzf /tmp/bitcoin.tgz -C /tmp; \
        install -m 0755 "/tmp/bitcoin-${BTC_VER}/bin/bitcoind" /home/auditor/.local/bin/bitcoind; \
        install -m 0755 "/tmp/bitcoin-${BTC_VER}/bin/bitcoin-cli" /home/auditor/.local/bin/bitcoin-cli; \
        rm -rf /tmp/bitcoin.tgz "/tmp/bitcoin-${BTC_VER}"; \
    fi; \
    fi

ENV PATH="/home/auditor/.venv/bin:${PATH}"
ENV VIRTUAL_ENV="/home/auditor/.venv"

# Login shells reset PATH; re-add every toolchain dir.
RUN { \
      echo 'export PATH="/home/auditor/.venv/bin:/home/auditor/.foundry/bin:/home/auditor/.aiken/bin:/home/auditor/.local/bin:/home/auditor/.cargo/bin:/home/auditor/.avm/bin:/home/auditor/.nargo/bin:/home/auditor/.fuelup/bin:/home/auditor/.local/share/solana/install/active_release/bin:$PATH"'; \
    } >> /home/auditor/.bashrc && \
    { \
      echo 'export PATH="/home/auditor/.venv/bin:/home/auditor/.foundry/bin:/home/auditor/.aiken/bin:/home/auditor/.local/bin:/home/auditor/.cargo/bin:/home/auditor/.avm/bin:/home/auditor/.nargo/bin:/home/auditor/.fuelup/bin:/home/auditor/.local/share/solana/install/active_release/bin:$PATH"'; \
    } >> /home/auditor/.profile

RUN mkdir -p /home/auditor/tools

USER root
RUN mkdir -p /workspace && chown auditor:auditor /workspace
COPY containers/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER auditor
WORKDIR /workspace

ENTRYPOINT ["docker-entrypoint.sh"]
