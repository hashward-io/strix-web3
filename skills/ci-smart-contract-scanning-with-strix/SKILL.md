---
name: ci-smart-contract-scanning-with-strix
description: Add smart-contract security scanning to CI/CD with Strix — a GitHub Actions or GitLab CI job that runs a diff-scoped audit on every pull request (any supported chain, not just Solidity/EVM), comments the findings on the PR, and uploads SARIF to code scanning, so vulnerable contract changes are caught before they merge. Uses the self-hosted open-source CLI inside your runner. Use when the user asks to add smart-contract security scanning, a contract audit gate, or automated contract review to their CI pipeline, pre-merge gate, or PR workflow.
license: Apache-2.0
metadata:
  author: usestrix
  homepage: https://docs.strix.ai
---

# Smart-contract scanning in CI with Strix

Run a diff-scoped Strix audit on every contract change, so a pull request that introduces a reentrancy, an access-control gap, or a rounding bug fails the gate before merge.

## GitHub Actions

```yaml
name: strix-audit
on:
  pull_request:
    paths: ["**/*.sol", "**/*.vy", "**/*.rs", "**/*.move", "**/*.cairo", "**/*.sw", "**/*.circom", "**/*.nr", "foundry.toml", "hardhat.config.*", "Anchor.toml", "Move.toml", "Scarb.toml", "Forc.toml"]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - name: Install Strix (from source)
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          git clone --depth 1 https://github.com/hashward-io/strix-web3 /tmp/strix-web3
          cd /tmp/strix-web3 && uv sync
          echo "/tmp/strix-web3/.venv/bin" >> "$GITHUB_PATH"

      - name: Build the sandbox image
        run: /tmp/strix-web3/scripts/docker.sh        # tags strix-sandbox:dev

      - name: Audit the change set
        env:
          STRIX_LLM: ${{ vars.STRIX_LLM }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          ETH_RPC_URL: ${{ secrets.ETH_RPC_URL }}
        run: strix -n -t . --scope-mode diff --diff-base "origin/${{ github.base_ref }}" --max-budget 15

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: strix_runs

      - name: Comment findings on the PR
        if: always()
        run: |
          gh pr comment "${{ github.event.number }}" \
            --body-file "$(ls -d strix_runs/*/ | tail -1)audit_report.md"
```

## GitLab CI

```yaml
strix-audit:
  image: docker:27
  services: [docker:27-dind]
  variables:
    STRIX_LLM: "$STRIX_LLM"
  script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - git clone --depth 1 https://github.com/hashward-io/strix-web3 /tmp/strix-web3
    - (cd /tmp/strix-web3 && uv sync)
    - export PATH="/tmp/strix-web3/.venv/bin:$PATH"
    - strix -n -t . --scope-mode diff --diff-base "$CI_MERGE_REQUEST_DIFF_BASE_SHA" --max-budget 15
  artifacts:
    when: always
    paths: [strix_runs/]
    reports:
      sast: strix_runs/**/findings.sarif
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Notes

- **Use `--scope-mode diff`** with the merge base. A full `deep` audit on every PR is slow and expensive; reserve it for release branches.
- **Requires Docker** in the runner (the audit runs in a multi-chain sandbox container).
- **Exit codes**: `0` clean, `1` fatal error, `2` findings. Gate on `2` to block on findings; treat `1` as a pipeline failure.
- **Budget**: `--max-budget` caps LLM spend per run. A `diff` scan on a small change set is cheap.
- **Secrets**: set `LLM_API_KEY` (and `ETH_RPC_URL` for fork PoCs) as CI secrets, never in the workflow file.
