from pathlib import Path

import pytest

from ansible_view.cli.main import build_parser, main


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# build_parser tests


def test_parser_defaults(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["site.yml"])
    assert args.playbook == "site.yml"
    assert args.tree is False
    assert args.execution is False
    assert args.debug is False


def test_parser_tree_flag():
    args = build_parser().parse_args(["site.yml", "--tree"])
    assert args.tree is True
    assert args.execution is False


def test_parser_execution_flag():
    args = build_parser().parse_args(["site.yml", "--execution"])
    assert args.execution is True
    assert args.tree is False


def test_parser_tree_and_execution_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["site.yml", "--tree", "--execution"])


def test_parser_debug_flag():
    args = build_parser().parse_args(["site.yml", "--debug"])
    assert args.debug is True


# main() routing tests — tree and execution modes


def test_main_tree_mode_returns_zero(tmp_path, capsys):
    pb = tmp_path / "site.yml"
    _write(
        pb, "- name: Web\n  hosts: all\n  tasks:\n    - name: t\n      debug:\n        msg: hi\n"
    )
    result = main([str(pb), "--tree"])
    assert result == 0
    captured = capsys.readouterr()
    assert "PLAYBOOK" in captured.out


def test_main_execution_mode_returns_zero(tmp_path, capsys):
    pb = tmp_path / "site.yml"
    _write(
        pb, "- name: Web\n  hosts: all\n  tasks:\n    - name: t\n      debug:\n        msg: hi\n"
    )
    result = main([str(pb), "--execution"])
    assert result == 0
    captured = capsys.readouterr()
    assert "PLAY" in captured.out


def test_main_tree_debug_mode(tmp_path, capsys):
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: Debug play\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: apt task\n"
        "      apt:\n"
        "        name: nginx\n"
        "        state: present\n"
        "      when: ansible_os_family == 'Debian'\n",
    )
    result = main([str(pb), "--tree", "--debug"])
    assert result == 0
    captured = capsys.readouterr()
    assert "when:" in captured.out


def test_main_missing_playbook_exits_nonzero(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "nonexistent.yml")])
    assert exc_info.value.code != 0


def test_main_execution_with_debug(tmp_path, capsys):
    pb = tmp_path / "site.yml"
    _write(
        pb,
        "- name: Exec debug\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: run me\n"
        "      debug:\n"
        "        msg: hello\n"
        "      register: out_var\n",
    )
    result = main([str(pb), "--execution", "--debug"])
    assert result == 0
    captured = capsys.readouterr()
    assert "register:" in captured.out


def test_main_module_entrypoint(tmp_path):
    import subprocess
    import sys

    pb = tmp_path / "site.yml"
    pb.write_text(
        "- name: p\n  hosts: all\n  tasks:\n    - name: t\n      debug:\n        msg: hi\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "ansible_view.cli.main", str(pb), "--tree"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "PLAYBOOK" in result.stdout


# iter_execution_nodes coverage (execution_graph_builder lines 30-37)


def test_iter_execution_nodes_yields_in_order():
    from ansible_view.execution.execution_graph_builder import (
        assign_execution_indices,
        iter_execution_nodes,
    )
    from ansible_view.models.node import Node

    task1 = Node(name="a", node_type="task")
    task2 = Node(name="b", node_type="task")
    section = Node(name="tasks", node_type="section")
    section.children = [task1, task2]
    role = Node(name="web", node_type="role")
    role_task = Node(name="c", node_type="task")
    role.children = [role_task]
    nodes = [section, role]
    assign_execution_indices(nodes, eager=True)
    result = list(iter_execution_nodes(nodes, eager=True))
    assert [n.name for n in result] == ["a", "b", "web", "c"]
