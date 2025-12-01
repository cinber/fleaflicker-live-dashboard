#!/usr/bin/env python3
"""Alias entry point that forwards to the unified CLI TUI command."""

from __future__ import annotations

import sys

from fleaflicker_dashboard.cli import main


def _with_tui_subcommand(argv: list[str]) -> list[str]:
    """Inject the 'tui' subcommand so legacy calls still work."""
    return ["tui", *argv]


def run() -> None:
    main(_with_tui_subcommand(sys.argv[1:]))


if __name__ == "__main__":
    run()
