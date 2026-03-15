from __future__ import annotations

import os
from typing import Callable, List, Optional

from ansible_view.models.node import Node
from ansible_view.models.role_node import RoleNode
from ansible_view.resolver.context import AnsibleConfig


def _role_candidates(
    role_name: str, collections_paths: List[str], collection: Optional[str]
) -> List[str]:
    candidates: List[str] = []
    if collection:
        parts = collection.split(".", 1)
        if len(parts) < 2:
            return candidates
        namespace, collection_name = parts
        for base in collections_paths:
            candidates.append(
                os.path.join(
                    base,
                    "ansible_collections",
                    namespace,
                    collection_name,
                    "roles",
                    role_name,
                )
            )
    elif "." in role_name:
        parts = role_name.split(".")
        if len(parts) >= 3:
            namespace, collection_name = parts[0], parts[1]
            role = ".".join(parts[2:])
            for base in collections_paths:
                candidates.append(
                    os.path.join(
                        base,
                        "ansible_collections",
                        namespace,
                        collection_name,
                        "roles",
                        role,
                    )
                )
    return candidates


class RoleResolver:
    def __init__(self, config: AnsibleConfig, task_file_loader: Callable[[str], List[Node]]):
        self.config = config
        self.task_file_loader = task_file_loader

    def _find_role_path(self, role_name: str, collection: Optional[str]) -> Optional[str]:
        for candidate in _role_candidates(role_name, self.config.collections_paths, collection):
            if os.path.isdir(candidate):
                return candidate
        for base in self.config.roles_path:
            candidate = os.path.join(base, role_name)
            if os.path.isdir(candidate):
                return candidate
        return None

    def _build_tasks_file_node(self, path: str, label: str) -> Node:
        node = Node(name=label, node_type="tasks_file", source_file=path)
        if not os.path.exists(path):
            node.error = f"file not found: {path}"
            return node

        node.set_child_loader(lambda: self.task_file_loader(path))
        return node

    def build_role_node(
        self,
        role_name: str,
        source_file: Optional[str],
        line_number: Optional[int],
        collection: Optional[str] = None,
        node_type: str = "role",
        tasks_from: Optional[str] = None,
        handlers_from: Optional[str] = None,
    ) -> RoleNode:
        node = RoleNode(
            name=role_name, node_type=node_type, source_file=source_file, line_number=line_number
        )
        role_path = self._find_role_path(role_name, collection)
        if not role_path:
            node.error = "role not found in configured role_paths"
            return node

        def load_children() -> List[Node]:
            children: List[Node] = []
            tasks_entry = tasks_from or "main.yml"
            handlers_entry = handlers_from or "main.yml"
            tasks_path = os.path.join(role_path, "tasks", tasks_entry)
            handlers_path = os.path.join(role_path, "handlers", handlers_entry)
            children.append(self._build_tasks_file_node(tasks_path, f"tasks/{tasks_entry}"))
            if os.path.exists(handlers_path):
                children.append(
                    self._build_tasks_file_node(handlers_path, f"handlers/{handlers_entry}")
                )
            return children

        node.set_child_loader(load_children)
        return node
