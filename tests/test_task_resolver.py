from pathlib import Path

from ansible_view.resolver.context import AnsibleConfig
from ansible_view.resolver.role_resolver import RoleResolver
from ansible_view.resolver.task_resolver import TaskResolver


def _make_resolver(base_dir: Path) -> TaskResolver:
    config = AnsibleConfig(
        config_path=None,
        roles_path=[str(base_dir / "roles")],
        collections_paths=[],
    )
    role_resolver = RoleResolver(config, task_file_loader=lambda path: [])
    return TaskResolver(str(base_dir), role_resolver)


def test_parse_standard_task(tmp_path: Path):
    resolver = _make_resolver(tmp_path)
    parent_file = str(tmp_path / "main.yml")
    tasks = [
        {"name": "Say hi", "debug": {"msg": "hello"}},
    ]

    nodes = resolver.parse_task_list(tasks, parent_file=parent_file)

    assert len(nodes) == 1
    node = nodes[0]
    assert node.name == "Say hi"
    assert node.module == "debug"
    assert node.args == {"msg": "hello"}
    assert node.source_file == parent_file


def test_parse_block_with_rescue_and_always(tmp_path: Path):
    resolver = _make_resolver(tmp_path)
    tasks = [
        {
            "name": "Block",
            "block": [{"name": "inside", "debug": {"msg": "x"}}],
            "rescue": [{"name": "recover", "debug": {"msg": "r"}}],
            "always": [{"name": "always", "debug": {"msg": "a"}}],
        }
    ]

    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "main.yml"))

    assert len(nodes) == 1
    block_node = nodes[0]
    assert block_node.node_type == "block"
    assert len(block_node.children) == 3
    assert block_node.children[1].name == "rescue"
    assert block_node.children[2].name == "always"
    assert block_node.children[1].children[0].name == "recover"
    assert block_node.children[2].children[0].name == "always"


def test_parse_include_tasks_real_file(tmp_path: Path):
    resolver = _make_resolver(tmp_path)
    parent_file = tmp_path / "main.yml"
    include_file = tmp_path / "included.yml"
    include_file.write_text("- name: included\n  debug: {msg: ok}\n", encoding="utf-8")

    tasks = [
        {"name": "Include", "include_tasks": "included.yml"},
    ]

    nodes = resolver.parse_task_list(tasks, parent_file=str(parent_file))
    include_node = nodes[0]
    assert include_node.node_type == "include_tasks"
    include_node.load_children()
    assert include_node.children
    file_node = include_node.children[0]
    assert file_node.source_file == str(include_file)
    file_node.load_children()
    assert any(child.name == "included" for child in file_node.children)


def test_collect_variables_from_jinja():
    resolver = _make_resolver(Path("."))
    task = {"name": "Test", "debug": {"msg": "hello {{ var_name }}"}}
    variables = resolver._collect_variables(task)

    assert variables is not None
    assert "var_name" in variables


def test_collect_variables_from_when():
    resolver = _make_resolver(Path("."))
    task = {
        "name": "Test",
        "debug": {"msg": "hello"},
        "when": "ansible_os_family == 'Debian'",
    }
    variables = resolver._collect_variables(task)

    assert variables is not None
    assert "ansible_os_family" in variables
