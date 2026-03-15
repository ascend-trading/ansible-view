from __future__ import annotations

import os
from typing import Any, List, Optional

from ansible_view.models.node import Node
from ansible_view.models.play_node import PlayNode
from ansible_view.parser.yaml_parser import get_line_number, load_yaml_file
from ansible_view.resolver.context import AnsibleConfig, load_ansible_config
from ansible_view.resolver.include_resolver import resolve_include_path
from ansible_view.resolver.role_resolver import RoleResolver
from ansible_view.resolver.task_resolver import TaskResolver


class PlaybookLoader:
    def __init__(
        self,
        playbook_path: str,
        config: Optional[AnsibleConfig] = None,
        visited: Optional[set[str]] = None,
    ):
        self.playbook_path = os.path.abspath(playbook_path)
        self.base_dir = os.path.dirname(self.playbook_path)
        self.config = config or load_ansible_config(self.base_dir)
        if visited is None:
            self._visited = {self.playbook_path}
        else:
            self._visited = visited
            self._visited.add(self.playbook_path)
        self._init_resolvers()

    @property
    def task_resolver(self) -> TaskResolver:
        return self._task_resolver

    @property
    def role_resolver(self) -> RoleResolver:
        return self._role_resolver

    def _init_resolvers(self) -> None:
        role_resolver = RoleResolver(self.config, self._load_task_file)
        task_resolver = TaskResolver(self.base_dir, role_resolver)
        task_resolver.set_playbook_loader(self._load_playbook_children)
        self._role_resolver = role_resolver
        self._task_resolver = task_resolver

    def load(self) -> Node:
        data = load_yaml_file(self.playbook_path)
        root = Node(
            name=os.path.basename(self.playbook_path),
            node_type="playbook",
            source_file=self.playbook_path,
        )
        if data is None:
            return root
        if not isinstance(data, list):
            root.children = [
                Node(
                    name="error",
                    node_type="error",
                    source_file=self.playbook_path,
                    error="expected a list of plays",
                )
            ]
            return root
        root.children = self._parse_playbook_entries(data, self.playbook_path)
        return root

    def _parse_playbook_entries(self, entries: List[Any], source_path: str) -> List[Node]:
        nodes: List[Node] = []
        for entry in entries:
            if isinstance(entry, dict) and (
                "import_playbook" in entry or "include_playbook" in entry
            ):
                nodes.append(self._parse_playbook_include(entry, source_path))
                continue
            if isinstance(entry, dict):
                nodes.append(self._parse_play(entry, source_path))
                continue
            nodes.append(
                Node(
                    name="error",
                    node_type="error",
                    source_file=source_path,
                    error="invalid play entry",
                )
            )
        return nodes

    def _parse_play(self, play: dict, source_path: str) -> PlayNode:
        name = play.get("name") or play.get("hosts") or "play"
        node = PlayNode(
            name=name,
            source_file=source_path,
            line_number=get_line_number(play),
        )
        raw_vars = play.get("vars")
        if isinstance(raw_vars, dict):
            clean = {k: v for k, v in raw_vars.items() if not str(k).startswith("__")}
            node.play_vars = clean if clean else None
        else:
            node.play_vars = None

        def load_children() -> List[Node]:
            children: List[Node] = []
            if play.get("gather_facts", True):
                children.append(
                    Node(
                        name="gather_facts",
                        node_type="gather_facts",
                        source_file=source_path,
                        line_number=get_line_number(play),
                    )
                )
            children.extend(self._parse_section(play, "pre_tasks", source_path))
            children.extend(self._parse_roles(play, source_path))
            children.extend(self._parse_section(play, "tasks", source_path))
            children.extend(self._parse_section(play, "post_tasks", source_path))
            children.extend(self._parse_handlers(play, source_path))
            return children

        node.set_child_loader(load_children)
        return node

    def _parse_roles(self, play: dict, source_path: str) -> List[Node]:
        roles = play.get("roles") or []
        nodes: List[Node] = []
        if not isinstance(roles, list):
            return nodes
        for role in roles:
            if isinstance(role, str):
                nodes.append(
                    self.role_resolver.build_role_node(
                        role, source_file=source_path, line_number=get_line_number(play)
                    )
                )
            elif isinstance(role, dict):
                role_name = role.get("role") or role.get("name")
                collection = role.get("collection")
                tasks_from = role.get("tasks_from")
                handlers_from = role.get("handlers_from")
                if role_name:
                    nodes.append(
                        self.role_resolver.build_role_node(
                            role_name,
                            source_file=source_path,
                            line_number=get_line_number(role),
                            collection=collection,
                            tasks_from=tasks_from,
                            handlers_from=handlers_from,
                        )
                    )
            else:
                nodes.append(
                    Node(
                        name="error",
                        node_type="error",
                        source_file=source_path,
                        error="invalid role entry",
                    )
                )
        return nodes

    def _parse_section(self, play: dict, key: str, source_path: str) -> List[Node]:
        tasks = play.get(key) or []
        if not tasks:
            return []
        section_node = Node(
            name=key,
            node_type="section",
            source_file=source_path,
            line_number=get_line_number(play),
        )
        if not isinstance(tasks, list):
            section_node.children = [
                Node(
                    name="error",
                    node_type="error",
                    source_file=source_path,
                    error=f"{key} should be a list",
                )
            ]
            return [section_node]
        section_node.children = self.task_resolver.parse_task_list(tasks, parent_file=source_path)
        return [section_node]

    def _parse_handlers(self, play: dict, source_path: str) -> List[Node]:
        handlers = play.get("handlers") or []
        if not handlers:
            return []
        section_node = Node(
            name="handlers",
            node_type="section",
            source_file=source_path,
            line_number=get_line_number(play),
        )
        if not isinstance(handlers, list):
            section_node.children = [
                Node(
                    name="error",
                    node_type="error",
                    source_file=source_path,
                    error="handlers should be a list",
                )
            ]
            return [section_node]
        section_node.children = self.task_resolver.parse_task_list(
            handlers, parent_file=source_path, task_kind="handler"
        )
        return [section_node]

    def _parse_playbook_include(self, entry: dict, source_path: str) -> Node:
        is_import = "import_playbook" in entry
        key = "import_playbook" if is_import else "include_playbook"
        include_value = entry.get(key)
        include_path = include_value if isinstance(include_value, str) else None
        include_path = include_path or "<unknown>"
        node_type = "import_playbook" if is_import else "include_playbook"
        node = Node(
            name=f"{node_type}: {include_path}",
            node_type=node_type,
            source_file=source_path,
            line_number=get_line_number(entry),
        )
        resolved = resolve_include_path(include_path, source_path, self.base_dir)
        if not resolved:
            node.error = "dynamic include cannot be resolved"
            return node

        def load_children() -> List[Node]:
            return self._load_playbook_children(resolved)

        node.set_child_loader(load_children)
        return node

    def _load_task_file(self, path: str) -> List[Node]:
        return self.task_resolver.load_task_file(path)

    def _load_playbook_children(self, path: str) -> List[Node]:
        if not os.path.exists(path):
            return [
                Node(
                    name="error",
                    node_type="error",
                    error=f"file not found: {path}",
                )
            ]
        if path in self._visited:
            return [
                Node(
                    name="error",
                    node_type="error",
                    error="circular include detected",
                )
            ]
        self._visited.add(path)
        loader = PlaybookLoader(path, config=self.config, visited=self._visited)
        root = loader.load()
        return root.children
