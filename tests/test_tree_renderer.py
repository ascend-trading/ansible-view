import io

from rich.console import Console

from ansible_view.models.node import Node
from ansible_view.ui.tree_renderer import (
    debug_lines,
    display_name,
    iter_play_nodes,
    render_execution,
    render_tree,
)


def _make_play(name="web play", children=None):
    play = Node(name=name, node_type="play")
    play.children = children or []
    return play


def _make_root(plays):
    root = Node(name="site.yml", node_type="playbook")
    root.children = plays
    return root


# display_name tests


def test_display_name_role():
    node = Node(name="nginx", node_type="role")
    assert display_name(node) == "role: nginx"


def test_display_name_include_tasks_with_colon():
    node = Node(name="include_tasks: setup.yml", node_type="include_tasks")
    assert display_name(node) == "include_tasks: setup.yml"


def test_display_name_include_tasks_without_colon():
    node = Node(name="setup.yml", node_type="include_tasks")
    assert display_name(node) == "include_tasks: setup.yml"


def test_display_name_gather_facts():
    node = Node(name="gather_facts", node_type="gather_facts")
    assert display_name(node) == "gather_facts"


def test_display_name_play():
    node = Node(name="Configure servers", node_type="play")
    assert display_name(node) == "play: Configure servers"


def test_display_name_handler():
    node = Node(name="restart nginx", node_type="handler")
    assert display_name(node) == "handler: restart nginx"


def test_display_name_block():
    node = Node(name="install block", node_type="block")
    assert display_name(node) == "block: install block"


def test_display_name_fallback():
    node = Node(name="my task", node_type="task")
    assert display_name(node) == "my task"


# debug_lines tests


def test_debug_lines_with_source_and_line():
    node = Node(name="t", node_type="task", source_file="/a/b.yml", line_number=5)
    lines = debug_lines(node)
    assert "file: /a/b.yml:5" in lines


def test_debug_lines_source_no_line():
    node = Node(name="t", node_type="task", source_file="/a/b.yml")
    lines = debug_lines(node)
    assert "file: /a/b.yml" in lines


def test_debug_lines_module_and_args():
    node = Node(name="t", node_type="task", module="apt", args={"name": "nginx"})
    lines = debug_lines(node)
    assert "module: apt" in lines
    assert "args:" in lines
    assert "  name: nginx" in lines


def test_debug_lines_when_tags_register():
    node = Node(
        name="t",
        node_type="task",
        when_conditions=["ansible_os_family == 'Debian'"],
        tags=["packages"],
        register_variable="result",
    )
    lines = debug_lines(node)
    assert any("when:" in line for line in lines)
    assert any("tags:" in line for line in lines)
    assert any("register:" in line for line in lines)


def test_debug_lines_play_vars():
    node = Node(name="p", node_type="play")
    node.play_vars = {"env": "production"}
    lines = debug_lines(node)
    assert "play_vars:" in lines
    assert "  env: production" in lines


def test_debug_lines_variables_header_is_vars_not_play_vars():
    node = Node(name="t", node_type="task", variables=["my_var"])
    node.play_vars = {"key": "val"}
    lines = debug_lines(node)
    assert lines.count("vars:") == 1
    assert "play_vars:" in lines


# iter_play_nodes tests


def test_iter_play_nodes_flat():
    play1 = _make_play("play1")
    play2 = _make_play("play2")
    root = _make_root([play1, play2])
    result = list(iter_play_nodes(root))
    assert [p.name for p in result] == ["play1", "play2"]


def test_iter_play_nodes_through_include_playbook():
    inner_play = _make_play("inner")
    wrapper = Node(name="include_playbook: other.yml", node_type="include_playbook")
    wrapper.children = [inner_play]
    root = _make_root([wrapper])
    result = list(iter_play_nodes(root))
    assert len(result) == 1
    assert result[0].name == "inner"


# render_tree output test


def _capture_render_tree(root, debug=False):
    buf = io.StringIO()
    console = Console(file=buf, highlight=False)
    from ansible_view.ui import tree_renderer

    original = tree_renderer.Console
    tree_renderer.Console = lambda: console
    try:
        render_tree(root, debug=debug)
    finally:
        tree_renderer.Console = original
    return buf.getvalue()


def test_render_tree_contains_play_name(tmp_path):
    play = _make_play("Configure web")
    task = Node(name="install nginx", node_type="task")
    play.children = [task]
    root = _make_root([play])
    output = _capture_render_tree(root)
    assert "PLAYBOOK: site.yml" in output
    assert "play: Configure web" in output
    assert "install nginx" in output


# render_execution output test


def test_render_execution_uses_execution_labels(capsys):
    play = _make_play("Deploy")
    task1 = Node(name="install", node_type="task")
    task2 = Node(name="start", node_type="task")
    play.children = [task1, task2]
    root = _make_root([play])

    buf = io.StringIO()
    console = Console(file=buf, highlight=False)
    from ansible_view.ui import tree_renderer

    original = tree_renderer.Console
    tree_renderer.Console = lambda: console
    try:
        render_execution(root)
    finally:
        tree_renderer.Console = original
    output = buf.getvalue()
    assert "PLAY 1: Deploy" in output
    assert "1 install" in output
    assert "2 start" in output


def test_debug_lines_loop():
    from ansible_view.models.node import Node
    from ansible_view.ui.tree_renderer import debug_lines

    node = Node(name="t", node_type="task", loop=["a", "b"])
    lines = debug_lines(node)
    assert any("loop:" in line for line in lines)


def test_debug_lines_notify():
    from ansible_view.models.node import Node
    from ansible_view.ui.tree_renderer import debug_lines

    node = Node(name="t", node_type="task", notify=["restart nginx"])
    lines = debug_lines(node)
    assert any("notify:" in line for line in lines)
    assert "restart nginx" in lines[-1]


def test_render_tree_error_node_includes_error_text(tmp_path, capsys):
    from ansible_view.resolver.playbook_loader import PlaybookLoader
    from ansible_view.ui.tree_renderer import render_tree

    pb = tmp_path / "site.yml"
    pb.write_text(
        "- name: Play\n  hosts: all\n  tasks:\n    - include_tasks: tasks/{{ dynamic }}.yml\n",
        encoding="utf-8",
    )
    root = PlaybookLoader(str(pb)).load()
    play = root.children[0]
    play.load_children()

    render_tree(root, debug=False)
    out = capsys.readouterr().out
    assert "ERROR" in out or "dynamic" in out
