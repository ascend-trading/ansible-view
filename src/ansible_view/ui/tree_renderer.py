from __future__ import annotations

from typing import List

from rich.console import Console
from rich.tree import Tree

from ansible_view.execution.execution_graph_builder import (
    assign_execution_indices,
    iter_execution_nodes,
)
from ansible_view.models.node import Node


def render_tree(root: Node, debug: bool = False) -> None:
    console = Console()
    tree = Tree(f"PLAYBOOK: {root.name}")
    for child in root.children:
        _add_tree_node(tree, child, debug)
    console.print(tree)


def render_execution(root: Node, debug: bool = False) -> None:
    console = Console()
    plays = list(iter_play_nodes(root))
    for idx, play in enumerate(plays, start=1):
        play.load_children()
        assign_execution_indices(play.children, eager=True)
        console.print(f"PLAY {idx}: {play.name}")
        for node in iter_execution_nodes(play.children, eager=True):
            label = node.execution_label() or ""
            line = f"  {label} {display_name(node)}".rstrip()
            console.print(line)
            if debug:
                for detail in debug_lines(node):
                    console.print(f"    {detail}")
        console.print("")


def iter_play_nodes(root: Node):
    def walk(node: Node):
        node.load_children()
        if node.node_type == "play":
            yield node
            return
        for child in node.children:
            yield from walk(child)

    for child in root.children:
        yield from walk(child)


def _add_tree_node(parent: Tree, node: Node, debug: bool) -> None:
    label = display_name(node)
    if node.error:
        label = f"{label} [red]ERROR: {node.error}[/red]"
    tree_node = parent.add(label)
    node.load_children()
    if debug:
        for detail in debug_lines(node):
            tree_node.add(f"[dim]{detail}[/dim]")
    for child in node.children:
        _add_tree_node(tree_node, child, debug)


def display_name(node: Node) -> str:
    if node.node_type in {"role", "include_role", "import_role"}:
        return f"role: {node.name}"
    if node.node_type in {"include_tasks", "import_tasks", "include_playbook", "import_playbook"}:
        if ":" in node.name:
            return node.name
        return f"{node.node_type}: {node.name}"
    if node.node_type == "gather_facts":
        return "gather_facts"
    if node.node_type == "play":
        return f"play: {node.name}"
    if node.node_type == "handler":
        return f"handler: {node.name}"
    if node.node_type == "block":
        return f"block: {node.name}"
    return node.name


def debug_lines(node: Node) -> List[str]:
    lines: List[str] = []
    if node.source_file:
        if node.line_number:
            lines.append(f"file: {node.source_file}:{node.line_number}")
        else:
            lines.append(f"file: {node.source_file}")
    if node.module:
        lines.append(f"module: {node.module}")
    if node.args:
        lines.append("args:")
        for key, value in node.args.items():
            lines.append(f"  {key}: {value}")
    if node.when_conditions:
        lines.append(f"when: {', '.join(node.when_conditions)}")
    if node.tags:
        lines.append(f"tags: {', '.join(node.tags)}")
    if node.variables:
        lines.append("vars:")
        for value in node.variables:
            lines.append(f"  {value}")
    if node.register_variable:
        lines.append(f"register: {node.register_variable}")
    if node.loop is not None:
        lines.append(f"loop: {node.loop}")
    if node.notify:
        lines.append(f"notify: {', '.join(node.notify)}")
    if node.play_vars:
        lines.append("play_vars:")
        for key, value in node.play_vars.items():
            if not str(key).startswith("__"):
                lines.append(f"  {key}: {value}")
    return lines
