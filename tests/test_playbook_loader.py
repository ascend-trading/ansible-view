from pathlib import Path

from ansible_view.resolver.playbook_loader import PlaybookLoader


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_playbook_loader_resolves_includes(tmp_path: Path):
    playbook = tmp_path / "site.yml"
    tasks_dir = tmp_path / "tasks"
    role_dir = tmp_path / "roles" / "web" / "tasks"

    _write(
        playbook,
        """
- name: Test play
  hosts: all
  tasks:
    - name: Include tasks
      include_tasks: tasks/setup.yml
    - name: Include role
      include_role:
        name: web
        tasks_from: install.yml
""".lstrip(),
    )
    _write(
        tasks_dir / "setup.yml",
        """
- name: setup task
  debug:
    msg: setup
""".lstrip(),
    )
    _write(
        role_dir / "install.yml",
        """
- name: role task
  debug:
    msg: role
""".lstrip(),
    )

    loader = PlaybookLoader(str(playbook))
    root = loader.load()

    assert root.children, "expected play nodes"
    play = root.children[0]
    play.load_children()

    tasks_section = next(node for node in play.children if node.name == "tasks")
    include_task = next(
        node for node in tasks_section.children if node.node_type == "include_tasks"
    )
    include_task.load_children()
    assert include_task.children, "include task should have file child"
    tasks_file = include_task.children[0]
    tasks_file.load_children()
    assert any(child.name == "setup task" for child in tasks_file.children)

    role_node = next(node for node in tasks_section.children if node.node_type == "include_role")
    role_node.load_children()
    tasks_file = next(child for child in role_node.children if "tasks/" in child.name)
    assert tasks_file.name == "tasks/install.yml"
    tasks_file.load_children()
    assert any(child.name == "role task" for child in tasks_file.children)
