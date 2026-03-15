from __future__ import annotations

import argparse
import sys
from typing import Literal

from ansible_view import __version__
from ansible_view.cli.command_view import run_view


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ansible-view",
        description="Inspect Ansible playbook execution flow from the terminal.",
    )
    parser.add_argument("playbook", help="Path to a playbook file")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tree", action="store_true", help="Render a static tree view")
    group.add_argument(
        "--execution",
        action="store_true",
        help="Render execution order output",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug metadata for tasks",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ansible-view {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    mode: Literal["tui", "tree", "execution"] = "tui"
    if args.tree:
        mode = "tree"
    elif args.execution:
        mode = "execution"

    try:
        return run_view(args.playbook, mode=mode, debug=args.debug)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except Exception as exc:  # pragma: no cover - cli guard
        print(f"ansible-view error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
