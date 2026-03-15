from __future__ import annotations

import os
from typing import Literal

from ansible_view.resolver.playbook_loader import PlaybookLoader
from ansible_view.ui.tree_renderer import render_execution, render_tree
from ansible_view.ui.tui_renderer import run_tui

Mode = Literal["tui", "tree", "execution"]


def run_view(playbook_path: str, mode: Mode, debug: bool) -> int:
    if not os.path.exists(playbook_path):
        raise FileNotFoundError(f"playbook not found: {playbook_path}")

    loader = PlaybookLoader(playbook_path)
    root = loader.load()

    if mode == "tree":
        render_tree(root, debug=debug)
    elif mode == "execution":
        render_execution(root, debug=debug)
    else:
        run_tui(root, debug=debug)  # pragma: no cover
    return 0
