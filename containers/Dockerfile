# ---------------------------------------------------------------------------
# Strix Web3 — Solidity / EVM audit sandbox
#
# Foundry-first image with the tooling a smart-contract auditor needs:
#   forge / cast / anvil, slither, aderyn, echidna, medusa, halmos,
#   solc, node + hardhat, and a Python venv with web3/eth-abi.
# ---------------------------------------------------------------------------
FROM debian:bookworm-slim

LABEL description="Strix Web3 sandbox — Foundry, Slither, Echidna, Medusa, Halmos, Aderyn"

ARG TARGETARCH

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl wget git jq unzip tar xz-utils \
        build-essential pkg-config \
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

# Foundry (forge, cast, anvil, chisel) + solc.
ENV PATH="/home/auditor/.foundry/bin:/home/auditor/.local/bin:${PATH}"
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /home/auditor/.foundry/bin/foundryup && \
    /home/auditor/.foundry/bin/forge --version

# Python audit venv: Slither + Halmos + web3 stack.
RUN python3 -m venv /home/auditor/.venv && \
    /home/auditor/.venv/bin/pip install --no-cache-dir --upgrade pip wheel && \
    /home/auditor/.venv/bin/pip install --no-cache-dir \
        slither-analyzer crytic-compile \
        halmos \
        web3 eth-abi eth-utils py-solc-x \
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
    curl -fsSL "https://github.com/Cyfrin/aderyn/releases/download/${TAG}/aderyn-${ADERYN_ARCH}-unknown-linux-gnu.tar.gz" -o /tmp/aderyn.tgz; \
    tar -xzf /tmp/aderyn.tgz -C /tmp; \
    mkdir -p /home/auditor/.local/bin; \
    install -m 0755 /tmp/aderyn /home/auditor/.local/bin/aderyn; \
    rm -f /tmp/aderyn /tmp/aderyn.tgz

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

# Medusa (coverage-guided stateful fuzzer).
RUN set -eux; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) MEDUSA_ARCH="amd64" ;; \
        arm64) MEDUSA_ARCH="arm64" ;; \
        *) echo "Unsupported arch for medusa" >&2; exit 1 ;; \
    esac; \
    TAG="$(curl -fsSL https://api.github.com/repos/crytic/medusa/releases/latest | jq -r .tag_name)"; \
    curl -fsSL "https://github.com/crytic/medusa/releases/download/${TAG}/medusa-linux-${MEDUSA_ARCH}.tar.gz" -o /tmp/medusa.tgz; \
    tar -xzf /tmp/medusa.tgz -C /tmp; \
    find /tmp -maxdepth 3 -type f -name 'medusa' -exec install -m 0755 {} /home/auditor/.local/bin/medusa \; ; \
    rm -rf /tmp/medusa /tmp/medusa.tgz; \
    /home/auditor/.local/bin/medusa --version || true

ENV PATH="/home/auditor/.venv/bin:${PATH}"
ENV VIRTUAL_ENV="/home/auditor/.venv"

# Login shells reset PATH; re-add the toolchain dirs.
RUN { \
      echo 'export PATH="/home/auditor/.venv/bin:/home/auditor/.foundry/bin:/home/auditor/.local/bin:$PATH"'; \
    } >> /home/auditor/.bashrc && \
    { \
      echo 'export PATH="/home/auditor/.venv/bin:/home/auditor/.foundry/bin:/home/auditor/.local/bin:$PATH"'; \
    } >> /home/auditor/.profile

RUN mkdir -p /home/auditor/tools /workspace

USER root
COPY containers/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER auditor
WORKDIR /workspace

ENTRYPOINT ["docker-entrypoint.sh"]
