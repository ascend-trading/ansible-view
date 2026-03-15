from pathlib import Path

from ansible_view.resolver.playbook_loader import PlaybookLoader


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_empty_file_returns_bare_root(tmp_path):
    pb = tmp_path / "site.yml"
    pb.write_text("", encoding="utf-8")
    root = PlaybookLoader(str(pb)).load()
    assert root.node_type == "playbook"
    assert root.children == []


def test_load_non_list_yaml_returns_error_child(tmp_path):
    pb = tmp_path / "site.yml"
    pb.write_text("key: value\n", encoding="utf-8")
    root = PlaybookLoader(str(pb)).load()
    assert len(root.children) == 1
    assert root.children[0].error == "expected a list of plays"


def test_invalid_play_entry_produces_error(tmp_path):
    pb = tmp_path / "site.yml"
    pb.write_text("- just_a_string\n", encoding="utf-8")
    root = PlaybookLoader(str(pb)).load()
    assert any(c.error == "invalid play entry" for c in root.children)


def test_gather_facts_false_omits_gather_node(tmp_path):
    pb = tmp_path / "site.yml"
    pb.write_text(
        "- name: No facts\n  hosts: all\n  gather_facts: false\n  tasks: []\n",
        encoding="utf-8",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    assert not any(c.node_type == "gather_facts" for c in play.children)


def test_pre_tasks_and_post_tasks_parsed(tmp_path):
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: Full play\n"
        "  hosts: all\n"
        "  pre_tasks:\n"
        "    - name: pre task\n"
        "      debug:\n"
        "        msg: pre\n"
        "  post_tasks:\n"
        "    - name: post task\n"
        "      debug:\n"
        "        msg: post\n",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    section_names = [c.name for c in play.children]
    assert "pre_tasks" in section_names
    assert "post_tasks" in section_names


def test_handlers_section_parsed(tmp_path):
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: Play with handler\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: do thing\n"
        "      debug:\n"
        "        msg: hi\n"
        "  handlers:\n"
        "    - name: restart nginx\n"
        "      service:\n"
        "        name: nginx\n"
        "        state: restarted\n",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    handlers_section = next((c for c in play.children if c.name == "handlers"), None)
    assert handlers_section is not None
    handlers_section.load_children()
    assert any(c.name == "restart nginx" for c in handlers_section.children)


def test_play_vars_stored_on_node(tmp_path):
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: Vars play\n  hosts: all\n  vars:\n    app_port: 8080\n  tasks: []\n",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    assert play.play_vars is not None
    assert play.play_vars.get("app_port") == 8080


def test_import_playbook_resolves_children(tmp_path):
    child_pb = tmp_path / "child.yml"
    _write(child_pb, "- name: Child play\n  hosts: all\n  tasks: []\n")
    parent_pb = tmp_path / "site.yml"
    _write(parent_pb, "- import_playbook: child.yml\n")
    root = PlaybookLoader(str(parent_pb)).load()
    assert len(root.children) == 1
    include_node = root.children[0]
    include_node.load_children()
    assert len(include_node.children) == 1
    assert include_node.children[0].name == "Child play"


def test_circular_include_detected(tmp_path):
    pb_a = tmp_path / "a.yml"
    pb_b = tmp_path / "b.yml"
    _write(pb_a, "- import_playbook: b.yml\n")
    _write(pb_b, "- import_playbook: a.yml\n")
    root = PlaybookLoader(str(pb_a)).load()
    include_node = root.children[0]
    include_node.load_children()
    inner = include_node.children[0]
    inner.load_children()
    assert any(c.error == "circular include detected" for c in inner.children)


def test_invalid_role_entry_produces_error(tmp_path):
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: Bad role\n  hosts: all\n  roles:\n    - 12345\n",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    assert any(c.error == "invalid role entry" for c in play.children)


def test_non_list_tasks_produces_error(tmp_path):
    pb = tmp_path / "site.yml"
    _write(pb, "- name: Bad tasks\n  hosts: all\n  tasks: not_a_list\n")
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()
    tasks_section = next((c for c in play.children if c.name == "tasks"), None)
    assert tasks_section is not None
    assert any(c.error and "list" in c.error for c in tasks_section.children)
