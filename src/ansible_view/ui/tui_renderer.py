from __future__ import annotations

import os
from typing import Any, List, Optional

from rich.console import Group as RichGroup
from rich.rule import Rule
from rich.syntax import Syntax
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Static, Tree

from ansible_view.execution.execution_graph_builder import assign_execution_indices
from ansible_view.models.node import Node
from ansible_view.ui.tree_renderer import debug_lines, display_name


class AnsibleViewApp(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("e", "toggle_execution", "Execution"),
        ("h", "toggle_hierarchy", "Hierarchy"),
        ("d", "toggle_debug", "Debug"),
        ("space", "toggle_expand", "Expand/Collapse"),
        ("enter", "toggle_expand", "Expand/Collapse"),
        ("[", "shrink_tree", "Narrow tree"),
        ("]", "expand_tree", "Widen tree"),
    ]

    CSS = """
    Horizontal {
        height: 1fr;
    }
    Tree {
        width: 2fr;
        border-right: solid $panel-lighten-2;
    }
    VerticalScroll {
        width: 1fr;
        background: $panel;
    }
    #details {
        padding: 1 2;
        width: 100%;
    }
    """

    def __init__(self, root: Node, debug: bool = False) -> None:
        super().__init__()
        self.root_node = root
        self.execution_mode = False
        self.debug_mode = debug
        self._tree_fr = 2

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Tree(f"PLAYBOOK: {self.root_node.name}", id="tree")
            with VerticalScroll():
                yield Static("", id="details")
        yield Footer()

    def on_mount(self) -> None:
        self._build_tree()

    def action_toggle_execution(self) -> None:
        self.execution_mode = not self.execution_mode
        self._build_tree()

    def action_toggle_hierarchy(self) -> None:
        self.execution_mode = False
        self._build_tree()

    def action_toggle_debug(self) -> None:
        self.debug_mode = not self.debug_mode
        self._update_details(self._selected_node())

    def action_shrink_tree(self) -> None:
        if self._tree_fr > 1:
            self._tree_fr -= 1
            self._apply_split()

    def action_expand_tree(self) -> None:
        if self._tree_fr < 6:
            self._tree_fr += 1
            self._apply_split()

    def _apply_split(self) -> None:
        self.query_one("#tree", Tree).styles.width = f"{self._tree_fr}fr"
        self.query_one(VerticalScroll).styles.width = "1fr"

    def action_toggle_expand(self) -> None:
        tree = self.query_one("#tree", Tree)
        if tree.cursor_node:
            tree.cursor_node.toggle()

    def _selected_node(self) -> Optional[Node]:
        tree = self.query_one("#tree", Tree)
        if tree.cursor_node:
            return tree.cursor_node.data
        return None

    def _build_tree(self) -> None:
        tree = self.query_one("#tree", Tree)
        self._clear_children(tree.root)
        tree.root.label = f"PLAYBOOK: {self.root_node.name}"
        tree.root.data = self.root_node
        self._refresh_execution_indices()
        for child in self.root_node.children:
            self._add_tree_node(tree.root, child)
        tree.root.expand()
        self._update_details(self._selected_node())

    def _refresh_execution_indices(self) -> None:
        for play in self.root_node.children:
            if play.has_lazy_children():
                continue
            assign_execution_indices(play.children, eager=False)

    def _add_tree_node(self, parent, node: Node) -> None:
        label = self._label_for(node)
        if node.error:
            label = f"{label} ERROR: {node.error}"
        tree_node = parent.add(label, data=node)
        if node.has_lazy_children():
            tree_node.allow_expand = True
            tree_node.add("loading...", data=None)
            return
        if node.children:
            tree_node.allow_expand = True
            for child in node.children:
                self._add_tree_node(tree_node, child)

    def _label_for(self, node: Node) -> str:
        base = display_name(node)
        if self.execution_mode and node.execution_label():
            return f"{node.execution_label()} {base}"
        return base

    def _clear_children(self, tree_node) -> None:
        tree_node.remove_children()

    def on_tree_node_expanded(self, event) -> None:
        node = event.node.data
        if not isinstance(node, Node):
            return
        if node.has_lazy_children():
            node.load_children()
            self._refresh_execution_indices()
            self._clear_children(event.node)
            for child in node.children:
                self._add_tree_node(event.node, child)
            event.node.expand()

    def on_tree_node_selected(self, event) -> None:
        node = event.node.data
        if isinstance(node, Node):
            self._update_details(node)

    def _update_details(self, node: Optional[Node]) -> None:
        details = self.query_one("#details", Static)
        if not node:
            details.update("")
            return

        renderables: List[Any] = []

        # --- metadata header ---
        meta = Text()
        meta.append(f"{node.node_type}", style="bold cyan")
        if node.source_file:
            meta.append("  ")
            meta.append(node.source_file, style="dim")
            if node.line_number:
                meta.append(f":{node.line_number}", style="yellow")
        if node.error:
            meta.append(f"\nERROR: {node.error}", style="bold red")
        renderables.append(meta)

        # --- debug metadata ---
        if self.debug_mode:
            debug = debug_lines(node)
            if debug:
                renderables.append(Rule(style="dim"))
                renderables.append(Text("\n".join(debug), style="dim"))

        # --- file source content ---
        if node.source_file and os.path.exists(node.source_file):
            renderables.append(Rule(style="dim"))
            renderables.append(
                Syntax.from_path(
                    node.source_file,
                    line_numbers=True,
                    highlight_lines={node.line_number} if node.line_number else set(),
                    theme="monokai",
                    word_wrap=False,
                )
            )

        details.update(RichGroup(*renderables))


def run_tui(root: Node, debug: bool = False) -> None:  # pragma: no cover
    app = AnsibleViewApp(root, debug=debug)
    app.run()
