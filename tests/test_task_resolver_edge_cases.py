from pathlib import Path

from ansible_view.resolver.context import AnsibleConfig
from ansible_view.resolver.role_resolver import RoleResolver
from ansible_view.resolver.task_resolver import TaskResolver


def _make_resolver(tmp_path: Path) -> TaskResolver:
    config = AnsibleConfig(config_path=None, roles_path=[], collections_paths=[])
    rr = RoleResolver(config, lambda p: [])
    return TaskResolver(str(tmp_path), rr)


def test_include_tasks_file_missing_at_load_time(tmp_path):
    sub = tmp_path / "sub.yml"
    sub.write_text("- name: task\n  debug:\n    msg: hi\n")
    resolver = _make_resolver(tmp_path)
    tasks = [{"include_tasks": "sub.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "site.yml"))
    node = nodes[0]
    sub.unlink()
    node.load_children()
    file_node = node.children[0]
    assert file_node.error is not None
    assert "file not found" in file_node.error


def test_include_playbook_in_task_list_dynamic_path_with_loader(tmp_path):
    resolver = _make_resolver(tmp_path)
    resolver.set_playbook_loader(lambda path: [])
    tasks = [{"include_playbook": "{{ env }}.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "site.yml"))
    assert nodes[0].error == "dynamic include cannot be resolved"


def test_extract_vars_digit_token_filtered(tmp_path):
    resolver = _make_resolver(tmp_path)
    tasks = [{"name": "digit task", "debug": {"msg": "{{ 123 }}"}}]
    nodes = resolver.parse_task_list(tasks, parent_file=None)
    variables = nodes[0].variables or []
    assert "123" not in variables
