"""Shell completion scripts and candidates for the Strix CLI."""

from __future__ import annotations

import sys
from typing import Any

from strix.interface.terminal_text import has_terminal_control, sanitize_terminal_text


_ROOT_COMMANDS = ("auth", "view", "completions", "completion")
_SCAN_FLAGS = (
    "-t",
    "--target",
    "--scan-mode",
    "--max-budget",
    "--instruction",
    "--max-turns",
    "-n",
    "--non-interactive",
    "--diff",
    "--diff-base",
    "--skill",
    "--workspace",
    "-h",
    "--help",
)


def run_completions(argv: list[str]) -> int:
    """Print a shell integration script or hidden completion candidates."""
    if argv and argv[0] == "--candidates":
        for candidate in completion_candidates(argv[1:]):
            sys.stdout.write(candidate + "\n")
        return 0
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.stdout.write(
            "Usage: strix completions <zsh|bash|fish>\n\n"
            "Enable tab completion for the current shell:\n"
            "  zsh:  source <(strix completions zsh)\n"
            "  bash: source <(strix completions bash)\n"
            "  fish: strix completions fish | source\n"
        )
        return 0
    shell = argv[0].lower()
    scripts = {"zsh": _zsh_script, "bash": _bash_script, "fish": _fish_script}
    generator = scripts.get(shell)
    if generator is None:
        sys.stderr.write(
            f"Unknown shell: {sanitize_terminal_text(shell)}. Choose zsh, bash, or fish.\n"
        )
        return 2
    sys.stdout.write(generator())
    return 0


def completion_candidates(words: list[str]) -> list[str]:
    """Return candidates for words after the ``strix`` executable."""
    prior, current = _split_cursor(words)
    candidates = (
        _matching((*_ROOT_COMMANDS, *_SCAN_FLAGS), current)
        if not prior
        else _matching(_SCAN_FLAGS, current)
    )
    # The line-oriented shell protocol cannot represent these names safely.
    return [candidate for candidate in candidates if not has_terminal_control(candidate)]


def _split_cursor(words: list[str]) -> tuple[list[str], str]:
    if not words:
        return [], ""
    return words[:-1], words[-1]


def _matching(candidates: Any, prefix: str) -> list[str]:
    return sorted({str(candidate) for candidate in candidates if str(candidate).startswith(prefix)})


def _zsh_script() -> str:
    return r"""#compdef strix
_strix() {
  local -a candidates
  candidates=("${(@f)$($words[1] completions --candidates "${words[@]:2}")}")
  _describe 'strix' candidates
}
compdef _strix strix
"""


def _bash_script() -> str:
    return r"""_strix_completion() {
  local -a candidates
  local candidate
  while IFS= read -r candidate; do
    candidates+=("$candidate")
  done < <(strix completions --candidates "${COMP_WORDS[@]:1:$COMP_CWORD}")
  COMPREPLY=("${candidates[@]}")
}
complete -F _strix_completion strix
"""


def _fish_script() -> str:
    return r"""function __strix_candidates
  set -l words (commandline -opc)
  set -e words[1]
  command strix completions --candidates $words (commandline -ct)
end
complete -c strix -f -a '(__strix_candidates)'
"""
