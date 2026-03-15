from __future__ import annotations

from typing import Iterable, List

from ansible_view.models.node import Node


def assign_execution_indices(nodes: List[Node], eager: bool = True) -> None:
    _assign(nodes, prefix=None, eager=eager, counter=0)


def _assign(
    nodes: List[Node],
    prefix: List[int] | None,
    eager: bool,
    counter: int,
) -> int:
    for node in nodes:
        if eager or not node.has_lazy_children():
            node.load_children()
        if node.is_executable():
            counter += 1
            node.execution_index = (prefix or []) + [counter]
            _assign(node.children, prefix=node.execution_index, eager=eager, counter=0)
        else:
            counter = _assign(node.children, prefix=prefix, eager=eager, counter=counter)
    return counter


def iter_execution_nodes(nodes: List[Node], eager: bool = True) -> Iterable[Node]:
    for node in nodes:
        if eager or not node.has_lazy_children():
            node.load_children()
        if node.is_executable():
            yield node
            yield from iter_execution_nodes(node.children, eager=eager)
        else:
            yield from iter_execution_nodes(node.children, eager=eager)
