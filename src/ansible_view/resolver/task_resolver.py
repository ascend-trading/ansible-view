from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from ansible_view.models.node import Node
from ansible_view.models.task_node import TaskNode
from ansible_view.parser.yaml_parser import get_line_number, load_yaml_file
from ansible_view.resolver.include_resolver import resolve_include_path
from ansible_view.resolver.role_resolver import RoleResolver

KNOWN_TASK_KEYS = {
    "name",
    "when",
    "tags",
    "register",
    "loop",
    "with_items",
    "notify",
    "vars",
    "args",
    "action",
    "delegate_to",
    "become",
    "become_user",
    "become_method",
    "environment",
    "include_tasks",
    "import_tasks",
    "include_role",
    "import_role",
    "include_playbook",
    "import_playbook",
    "block",
    "rescue",
    "always",
    "role",
}

# Bare action names that trigger special parsing (dispatch table keys).
# Matched against the last dotted segment so FQCN forms like
# ansible.builtin.import_role are handled transparently.
_DISPATCH_ACTIONS = {
    "block",
    "include_tasks",
    "import_tasks",
    "include_role",
    "import_role",
    "include_playbook",
    "import_playbook",
}


def _bare(key: str) -> str:
    """Return the bare action name, stripping any FQCN prefix."""
    return key.rsplit(".", 1)[-1]


def _find_action_key(task: Dict[str, Any]) -> Optional[str]:
    """Return the first task key whose bare name is a dispatch action, or None."""
    for key in task:
        if _bare(key) in _DISPATCH_ACTIONS:
            return key
    return None


class TaskResolver:
    def __init__(self, base_dir: str, role_resolver: RoleResolver):
        self.base_dir = base_dir
        self.role_resolver = role_resolver
        self.playbook_loader = None

    def set_playbook_loader(self, loader) -> None:
        self.playbook_loader = loader

    def load_task_file(self, path: str) -> List[Node]:
        data = load_yaml_file(path)
        if data is None:
            return []
        if not isinstance(data, list):
            return [
                Node(
                    name="error",
                    node_type="error",
                    source_file=path,
                    error="expected a list of tasks",
                )
            ]
        return self.parse_task_list(data, parent_file=path)

    def parse_task_list(
        self,
        task_list: List[Any],
        parent_file: Optional[str],
        task_kind: str = "task",
    ) -> List[Node]:
        nodes: List[Node] = []
        for task in task_list:
            if not isinstance(task, dict):
                nodes.append(
                    Node(
                        name="error",
                        node_type="error",
                        source_file=parent_file,
                        error="invalid task entry",
                    )
                )
                continue
            action_key = _find_action_key(task)
            bare = _bare(action_key) if action_key else None
            if bare == "block":
                nodes.append(self._parse_block(task, parent_file))
            elif bare in ("include_tasks", "import_tasks"):
                nodes.append(self._parse_include_tasks(task, parent_file, action_key))
            elif bare in ("include_role", "import_role"):
                nodes.append(self._parse_include_role(task, parent_file, action_key))
            elif bare in ("include_playbook", "import_playbook"):
                nodes.append(self._parse_include_playbook(task, parent_file, action_key))
            else:
                nodes.append(self._parse_standard_task(task, parent_file, task_kind))
        return nodes

    def _parse_block(self, task: Dict[str, Any], parent_file: Optional[str]) -> Node:
        name = task.get("name", "block")
        node = Node(
            name=name,
            node_type="block",
            source_file=parent_file,
            line_number=get_line_number(task),
        )
        children: List[Node] = []
        block_tasks = task.get("block") or []
        children.extend(self.parse_task_list(block_tasks, parent_file=parent_file))
        rescue_tasks = task.get("rescue") or []
        if rescue_tasks:
            rescue_node = Node(name="rescue", node_type="section")
            rescue_node.children = self.parse_task_list(rescue_tasks, parent_file=parent_file)
            children.append(rescue_node)
        always_tasks = task.get("always") or []
        if always_tasks:
            always_node = Node(name="always", node_type="section")
            always_node.children = self.parse_task_list(always_tasks, parent_file=parent_file)
            children.append(always_node)
        node.children = children
        return node

    def _parse_include_tasks(
        self,
        task: Dict[str, Any],
        parent_file: Optional[str],
        action_key: Optional[str] = None,
    ) -> Node:
        key = action_key or ("import_tasks" if "import_tasks" in task else "include_tasks")
        is_import = _bare(key) == "import_tasks"
        include_value = task.get(key)
        include_path = None
        if isinstance(include_value, str):
            include_path = include_value
        elif isinstance(include_value, dict):
            include_path = include_value.get("file") or include_value.get("name")
        include_path = include_path or "<unknown>"

        node_type = "import_tasks" if is_import else "include_tasks"  # always bare
        task_name = task.get("name")
        display_name = (
            f"{task_name} ({include_path})" if task_name else f"{node_type}: {include_path}"
        )
        node = TaskNode(
            name=display_name,
            node_type=node_type,
            source_file=parent_file,
            line_number=get_line_number(task),
        )
        self._apply_task_metadata(node, task)

        resolved = resolve_include_path(include_path, parent_file, self.base_dir)
        if not resolved:
            node.error = "dynamic include cannot be resolved"
            return node

        def load_children() -> List[Node]:
            file_node = Node(name=include_path, node_type="tasks_file", source_file=resolved)
            if not file_node.source_file or not os.path.exists(file_node.source_file):
                file_node.error = f"file not found: {resolved}"
                return [file_node]
            source: str = file_node.source_file  # type: ignore[assignment]
            file_node.set_child_loader(lambda: self.load_task_file(source))
            return [file_node]

        node.set_child_loader(load_children)
        return node

    def _parse_include_role(
        self,
        task: Dict[str, Any],
        parent_file: Optional[str],
        action_key: Optional[str] = None,
    ) -> Node:
        key = action_key or ("import_role" if "import_role" in task else "include_role")
        is_import = _bare(key) == "import_role"
        role_spec = task.get(key)
        role_name = None
        collection = None
        tasks_from = None
        handlers_from = None
        if isinstance(role_spec, str):
            role_name = role_spec
        elif isinstance(role_spec, dict):
            role_name = role_spec.get("name") or role_spec.get("role")
            collection = role_spec.get("collection")
            tasks_from = role_spec.get("tasks_from")
            handlers_from = role_spec.get("handlers_from")
        role_name = role_name or "<unknown>"

        node_type = "import_role" if is_import else "include_role"  # always bare
        node = self.role_resolver.build_role_node(
            role_name,
            source_file=parent_file,
            line_number=get_line_number(task),
            collection=collection,
            node_type=node_type,
            tasks_from=tasks_from,
            handlers_from=handlers_from,
        )
        self._apply_task_metadata(node, task)
        return node

    def _parse_include_playbook(
        self,
        task: Dict[str, Any],
        parent_file: Optional[str],
        action_key: Optional[str] = None,
    ) -> Node:
        key = action_key or ("import_playbook" if "import_playbook" in task else "include_playbook")
        is_import = _bare(key) == "import_playbook"
        value = task.get(key)
        include_path = value if isinstance(value, str) else None
        include_path = include_path or "<unknown>"

        node_type = "import_playbook" if is_import else "include_playbook"
        task_name = task.get("name")
        display_name = (
            f"{task_name} ({include_path})" if task_name else f"{node_type}: {include_path}"
        )
        node = TaskNode(
            name=display_name,
            node_type=node_type,
            source_file=parent_file,
            line_number=get_line_number(task),
        )
        self._apply_task_metadata(node, task)

        if not self.playbook_loader:
            node.error = "playbook loader unavailable"
            return node

        resolved = resolve_include_path(include_path, parent_file, self.base_dir)
        if not resolved:
            node.error = "dynamic include cannot be resolved"
            return node

        def load_children() -> List[Node]:
            try:
                return self.playbook_loader(resolved)
            except Exception as exc:  # pragma: no cover - defensive
                return [Node(name="error", node_type="error", error=str(exc))]

        node.set_child_loader(load_children)
        return node

    def _parse_standard_task(
        self, task: Dict[str, Any], parent_file: Optional[str], task_kind: str
    ) -> Node:
        name = task.get("name") or "unnamed task"
        module, args = self._extract_action(task)
        node = TaskNode(
            name=name,
            node_type=task_kind,
            source_file=parent_file,
            line_number=get_line_number(task),
            module=module,
            args=args,
        )
        self._apply_task_metadata(node, task)
        return node

    def _apply_task_metadata(self, node: Node, task: Dict[str, Any]) -> None:
        when = task.get("when")
        tags = task.get("tags")
        notify = task.get("notify")
        loop = task.get("loop") or task.get("with_items")
        node.when_conditions = self._normalize_list(when)
        node.tags = self._normalize_list(tags)
        node.notify = self._normalize_list(notify)
        node.register_variable = task.get("register")
        node.loop = loop
        node.variables = self._collect_variables(task)

    def _normalize_list(self, value: Any) -> Optional[List[str]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    def _extract_action(
        self, task: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        if "action" in task:
            action = task.get("action")
            if isinstance(action, str):
                return action, None
            if isinstance(action, dict):
                for key, value in action.items():
                    if isinstance(value, dict):
                        return key, self._strip_internal_keys(value)
                    return key, {"__raw__": value}
        for key, value in task.items():
            if key in KNOWN_TASK_KEYS or key.startswith("__"):
                continue
            if isinstance(value, dict):
                return key, self._strip_internal_keys(value)
            return key, {"__raw__": value}
        return None, None

    def _strip_internal_keys(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                k: self._strip_internal_keys(v) for k, v in value.items() if not k.startswith("__")
            }
        if isinstance(value, list):
            return [self._strip_internal_keys(item) for item in value]
        return value

    def _collect_variables(self, task: Dict[str, Any]) -> Optional[List[str]]:
        variables: set[str] = set()
        for key, value in task.items():
            if key.startswith("__"):
                continue
            variables.update(self._extract_vars_from_value(value, key))
        if not variables:
            return None
        return sorted(variables)

    def _extract_vars_from_value(self, value: Any, key: str) -> set[str]:
        if isinstance(value, str):
            return set(self._extract_vars_from_string(value, key))
        if isinstance(value, list):
            found: set[str] = set()
            for item in value:
                found.update(self._extract_vars_from_value(item, key))
            return found
        if isinstance(value, dict):
            found = set()
            for sub_key, sub_value in value.items():
                found.update(self._extract_vars_from_value(sub_value, sub_key))
            return found
        return set()

    def _extract_vars_from_string(self, value: str, key: str) -> List[str]:
        token_re = re.compile(r"\b[A-Za-z_][A-Za-z0-9_.]*\b")
        jinja_re = re.compile(r"{{\s*([^}]+)\s*}}")
        jinja_stmt_re = re.compile(r"{%\s*([^}]+)\s*%}")
        keywords = {
            "and",
            "or",
            "not",
            "in",
            "is",
            "true",
            "false",
            "none",
            "omit",
            "True",
            "False",
            "None",
        }
        expressions: List[str] = []
        if "{{" in value or "{%" in value:
            expressions.extend(jinja_re.findall(value))
            expressions.extend(jinja_stmt_re.findall(value))
            if not expressions:
                expressions.append(value)
        elif key in {"when", "loop", "with_items", "until"}:
            expressions.append(value)
        else:
            return []

        variables: List[str] = []
        for expr in expressions:
            for token in token_re.findall(expr):
                if token in keywords:
                    continue
                variables.append(token)
        return variables
