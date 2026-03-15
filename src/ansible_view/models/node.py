from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

EXECUTABLE_TYPES = {
    "task",
    "include_tasks",
    "import_tasks",
    "include_role",
    "import_role",
    "role",
    "gather_facts",
    "handler",
    "include_playbook",
    "import_playbook",
}


@dataclass
class Node:
    name: str
    node_type: str
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    module: Optional[str] = None
    args: Optional[Dict] = None
    when_conditions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    register_variable: Optional[str] = None
    loop: Optional[str] = None
    notify: Optional[List[str]] = None
    variables: Optional[List[str]] = None
    play_vars: Optional[Dict] = None
    error: Optional[str] = None
    execution_index: Optional[List[int]] = None
    children: List["Node"] = field(default_factory=list)
    _child_loader: Optional[Callable[[], List["Node"]]] = None
    _children_loaded: bool = False

    def set_child_loader(self, loader: Callable[[], List["Node"]]) -> None:
        self._child_loader = loader
        self._children_loaded = False

    def has_lazy_children(self) -> bool:
        return self._child_loader is not None and not self._children_loaded

    def load_children(self) -> None:
        if self._child_loader and not self._children_loaded:
            try:
                self.children = self._child_loader()
            except Exception as exc:
                self.children = [
                    Node(
                        name="error",
                        node_type="error",
                        error=str(exc),
                    )
                ]
            self._children_loaded = True

    def is_executable(self) -> bool:
        return self.node_type in EXECUTABLE_TYPES

    def execution_label(self) -> Optional[str]:
        if not self.execution_index:
            return None
        return ".".join(str(part) for part in self.execution_index)
