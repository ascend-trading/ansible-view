from pathlib import Path

from ansible_view.resolver.playbook_loader import PlaybookLoader


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_roles_non_list_is_skipped(tmp_path):
    pb = tmp_path / "site.yml"
    _write(pb, "- name: p\n  hosts: all\n  roles: not_a_list\n")
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    assert not any(
        c.node_type in {"role", "error"}
        for c in play.children
        if c.name not in {"gather_facts", "tasks", "pre_tasks", "post_tasks", "handlers"}
    )


def test_string_role_in_roles_list(tmp_path):
    role_dir = tmp_path / "roles" / "nginx" / "tasks"
    role_dir.mkdir(parents=True)
    (role_dir / "main.yml").write_text("- name: install\n  debug:\n    msg: hi\n")
    pb = tmp_path / "site.yml"
    _write(pb, "- name: p\n  hosts: all\n  roles:\n    - nginx\n")
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    role_nodes = [c for c in play.children if c.node_type == "role"]
    assert len(role_nodes) == 1
    assert role_nodes[0].name == "nginx"


def test_dict_role_in_roles_list(tmp_path):
    role_dir = tmp_path / "roles" / "nginx" / "tasks"
    role_dir.mkdir(parents=True)
    (role_dir / "main.yml").write_text("- name: install\n  debug:\n    msg: hi\n")
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: p\n  hosts: all\n  roles:\n    - role: nginx\n      tasks_from: main.yml\n",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    role_nodes = [c for c in play.children if c.node_type == "role"]
    assert len(role_nodes) == 1
    assert role_nodes[0].name == "nginx"


def test_handlers_non_list_produces_error(tmp_path):
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: p\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: t\n"
        "      debug:\n"
        "        msg: hi\n"
        "  handlers: not_a_list\n",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    handlers_section = next((c for c in play.children if c.name == "handlers"), None)
    assert handlers_section is not None
    assert any("list" in (c.error or "") for c in handlers_section.children)


def test_dynamic_import_playbook_sets_error(tmp_path):
    pb = tmp_path / "site.yml"
    _write(pb, "- import_playbook: '{{ env }}.yml'\n")
    root = PlaybookLoader(str(pb)).load()
    assert len(root.children) == 1
    node = root.children[0]
    assert node.error == "dynamic include cannot be resolved"


def test_load_playbook_children_file_not_found(tmp_path):
    pb = tmp_path / "site.yml"
    _write(pb, "- import_playbook: missing.yml\n")
    root = PlaybookLoader(str(pb)).load()
    include_node = root.children[0]
    include_node.load_children()
    assert len(include_node.children) == 1
    assert "file not found" in include_node.children[0].error
