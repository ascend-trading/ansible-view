from pathlib import Path

from ansible_view.models.node import Node
from ansible_view.resolver.context import AnsibleConfig
from ansible_view.resolver.role_resolver import RoleResolver
from ansible_view.resolver.task_resolver import TaskResolver


def _make_resolver(tmp_path: Path) -> TaskResolver:
    config = AnsibleConfig(config_path=None, roles_path=[], collections_paths=[])
    rr = RoleResolver(config, lambda p: [])
    return TaskResolver(str(tmp_path), rr)


# load_task_file error paths


def test_load_task_file_empty_returns_empty(tmp_path):
    f = tmp_path / "empty.yml"
    f.write_text("")
    resolver = _make_resolver(tmp_path)
    result = resolver.load_task_file(str(f))
    assert result == []


def test_load_task_file_non_list_returns_error(tmp_path):
    f = tmp_path / "bad.yml"
    f.write_text("key: value\n")
    resolver = _make_resolver(tmp_path)
    result = resolver.load_task_file(str(f))
    assert len(result) == 1
    assert result[0].error == "expected a list of tasks"


# parse_task_list — non-dict entry


def test_parse_task_list_non_dict_entry_is_error(tmp_path):
    resolver = _make_resolver(tmp_path)
    nodes = resolver.parse_task_list(["just_a_string"], parent_file=None)
    assert len(nodes) == 1
    assert nodes[0].error == "invalid task entry"


# include_playbook inside task list


def test_include_playbook_in_task_list_no_loader(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"include_playbook": "other.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "site.yml"))
    assert len(nodes) == 1
    assert nodes[0].error == "playbook loader unavailable"


def test_import_playbook_in_task_list_with_loader(tmp_path):
    child = tmp_path / "child.yml"
    child.write_text("- name: Child\n  hosts: all\n  tasks: []\n")
    resolver = _make_resolver(tmp_path)
    resolver.set_playbook_loader(lambda path: [Node(name="child-play", node_type="play")])
    tasks = [{"import_playbook": "child.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "site.yml"))
    assert len(nodes) == 1
    nodes[0].load_children()
    assert nodes[0].children[0].name == "child-play"


# include_tasks with dict form {file: path}


def test_include_tasks_dict_form(tmp_path):
    sub = tmp_path / "sub.yml"
    sub.write_text("- name: sub\n  debug:\n    msg: hi\n")
    resolver = _make_resolver(tmp_path)
    tasks = [{"include_tasks": {"file": "sub.yml"}}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "site.yml"))
    assert len(nodes) == 1
    nodes[0].load_children()
    file_node = nodes[0].children[0]
    file_node.load_children()
    assert any(c.name == "sub" for c in file_node.children)


# include_tasks with dynamic Jinja path


def test_include_tasks_dynamic_path_sets_error(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"include_tasks": "tasks/{{ env }}.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "site.yml"))
    assert nodes[0].error == "dynamic include cannot be resolved"


# include_role with string spec


def test_include_role_string_spec(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"include_role": "nginx"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "site.yml"))
    assert len(nodes) == 1
    assert nodes[0].name == "nginx"
    assert nodes[0].error == "role not found in configured role_paths"


# _extract_action variants


def test_extract_action_string_action(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "run it", "action": "shell echo hi"}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].module == "shell echo hi"
    assert nodes[0].args is None


def test_extract_action_dict_action_with_dict_args(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "run apt", "action": {"apt": {"name": "nginx", "state": "present"}}}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].module == "apt"
    assert nodes[0].args == {"name": "nginx", "state": "present"}


def test_extract_action_dict_action_with_raw_value(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "raw action", "action": {"shell": "echo hi"}}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].module == "shell"


def test_extract_action_module_with_raw_string_value(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "raw debug", "debug": "msg=hello"}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].module == "debug"
    assert nodes[0].args == {"__raw__": "msg=hello"}


def test_extract_action_no_module_returns_none(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "no module task", "when": "true", "tags": ["t"]}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].module is None
    assert nodes[0].args is None


# _strip_internal_keys with list


def test_strip_internal_keys_with_list(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "list mod", "mymod": {"items": [{"key": "val", "__line__": 5}]}}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].module == "mymod"
    assert nodes[0].args == {"items": [{"key": "val"}]}


# _extract_vars_from_value with list value


def test_extract_vars_from_list_value(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "loop task", "debug": {"msg": "hi"}, "loop": ["{{ item_var }}"]}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].variables is not None
    assert "item_var" in nodes[0].variables


# _extract_vars_from_string — jinja keyword filtering


def test_extract_vars_keywords_filtered(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [
        {
            "name": "keyword filter",
            "debug": {"msg": "hi"},
            "when": "ansible_os == 'Debian' and not skip_it",
        }
    ]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert nodes[0].variables is not None
    assert "and" not in nodes[0].variables
    assert "not" not in nodes[0].variables
    assert "ansible_os" in nodes[0].variables
    assert "skip_it" in nodes[0].variables


# _extract_vars_from_string — jinja present but no findall match fallback


def test_extract_vars_malformed_jinja_fallback(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "malformed", "debug": {"msg": "{{ unclosed"}}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    assert isinstance(nodes[0].variables, (list, type(None)))
