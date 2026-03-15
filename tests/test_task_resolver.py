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


# ---------------------------------------------------------------------------
# FQCN dispatch tests
# ---------------------------------------------------------------------------


def test_fqcn_import_tasks(tmp_path: Path):
    """ansible.builtin.import_tasks (FQCN) should be handled like import_tasks."""
    resolver = _make_resolver(tmp_path)
    include_file = tmp_path / "setup.yml"
    include_file.write_text("- name: setup step\n  debug: {msg: ok}\n", encoding="utf-8")

    tasks = [{"ansible.builtin.import_tasks": "setup.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "main.yml"))

    assert len(nodes) == 1
    assert nodes[0].node_type == "import_tasks"


def test_fqcn_include_tasks(tmp_path: Path):
    """ansible.builtin.include_tasks (FQCN) should be handled like include_tasks."""
    resolver = _make_resolver(tmp_path)
    include_file = tmp_path / "extra.yml"
    include_file.write_text("- name: extra step\n  debug: {msg: ok}\n", encoding="utf-8")

    tasks = [{"ansible.builtin.include_tasks": "extra.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "main.yml"))

    assert len(nodes) == 1
    assert nodes[0].node_type == "include_tasks"


def test_fqcn_import_role(tmp_path: Path):
    """ansible.builtin.import_role (FQCN) should be handled like import_role."""
    roles_dir = tmp_path / "roles" / "myrole" / "tasks"
    roles_dir.mkdir(parents=True)
    (roles_dir / "main.yml").write_text("- name: role task\n  debug: {msg: hi}\n", encoding="utf-8")

    resolver = _make_resolver(tmp_path)
    tasks = [{"ansible.builtin.import_role": {"name": "myrole"}}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "main.yml"))

    assert len(nodes) == 1
    assert nodes[0].node_type == "import_role"


def test_fqcn_include_role(tmp_path: Path):
    """ansible.builtin.include_role (FQCN) should be handled like include_role."""
    roles_dir = tmp_path / "roles" / "otherrole" / "tasks"
    roles_dir.mkdir(parents=True)
    (roles_dir / "main.yml").write_text("- name: other task\n  debug: {msg: y}\n", encoding="utf-8")

    resolver = _make_resolver(tmp_path)
    tasks = [{"ansible.builtin.include_role": {"name": "otherrole"}}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "main.yml"))

    assert len(nodes) == 1
    assert nodes[0].node_type == "include_role"


def test_fqcn_block(tmp_path: Path):
    """ansible.builtin.block (FQCN) should be dispatched as a block."""
    resolver = _make_resolver(tmp_path)
    tasks = [
        {
            "ansible.builtin.block": [{"name": "inside", "debug": {"msg": "x"}}],
        }
    ]
    nodes = resolver.parse_task_list(tasks, parent_file=str(tmp_path / "main.yml"))

    assert len(nodes) == 1
    assert nodes[0].node_type == "block"
    assert len(nodes[0].children) == 1
    assert nodes[0].children[0].name == "inside"


def test_import_tasks_fallback_to_base_dir(tmp_path: Path):
    """import_tasks with a path that doesn't exist next to the parent file but
    does exist at the playbook root should still resolve correctly."""
    resolver = _make_resolver(tmp_path)
    # Task file lives at <base_dir>/tasks/common.yml
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    common_file = tasks_dir / "common.yml"
    common_file.write_text("- name: common step\n  debug: {msg: ok}\n", encoding="utf-8")

    # Parent file is inside a role's tasks directory (doesn't have tasks/common.yml nearby).
    role_tasks_dir = tmp_path / "roles" / "myrole" / "tasks"
    role_tasks_dir.mkdir(parents=True)

    tasks = [{"import_tasks": "tasks/common.yml"}]
    nodes = resolver.parse_task_list(tasks, parent_file=str(role_tasks_dir / "main.yml"))

    assert len(nodes) == 1
    node = nodes[0]
    assert node.node_type == "import_tasks"
    # Should resolve and be expandable (not carry an error).
    assert node.error is None
    node.load_children()
    assert node.children  # file_node present
    assert node.children[0].source_file == str(common_file)
