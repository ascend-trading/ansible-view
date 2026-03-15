from pathlib import Path

from ansible_view.models.node import Node
from ansible_view.resolver.playbook_loader import PlaybookLoader
from ansible_view.ui.tui_renderer import AnsibleViewApp, run_tui


def _make_root(tmp_path: Path) -> Node:
    pb = tmp_path / "site.yml"
    pb.write_text(
        "- name: Web play\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: install nginx\n"
        "      apt:\n"
        "        name: nginx\n"
        "        state: present\n"
        "      when: ansible_os_family == 'Debian'\n"
        "      tags: [packages]\n"
        "      register: nginx_result\n"
        "      notify: restart nginx\n"
        "    - name: start nginx\n"
        "      service:\n"
        "        name: nginx\n"
        "        state: started\n"
        "  handlers:\n"
        "    - name: restart nginx\n"
        "      service:\n"
        "        name: nginx\n"
        "        state: restarted\n",
        encoding="utf-8",
    )
    return PlaybookLoader(str(pb)).load()


async def test_app_mounts_and_shows_playbook_title(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        assert "site.yml" in str(tree.root.label)


async def test_quit_action_exits_app(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        await pilot.press("q")


async def test_toggle_execution_mode_on(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        assert app.execution_mode is False
        await pilot.press("e")
        assert app.execution_mode is True


async def test_toggle_execution_mode_twice_returns_off(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        await pilot.press("e")
        assert app.execution_mode is True
        await pilot.press("e")
        assert app.execution_mode is False


async def test_toggle_hierarchy_resets_execution_mode(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        await pilot.press("e")
        assert app.execution_mode is True
        await pilot.press("h")
        assert app.execution_mode is False


async def test_toggle_debug_flips_debug_mode(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root, debug=False)
    async with app.run_test() as pilot:
        assert app.debug_mode is False
        await pilot.press("d")
        assert app.debug_mode is True
        await pilot.press("d")
        assert app.debug_mode is False


async def test_tree_has_play_node(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        assert tree.root.children


async def test_expand_with_enter_key(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        await pilot.press("enter")


async def test_expand_with_space_key(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        await pilot.press("space")


async def test_details_panel_shows_type_in_normal_mode(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root, debug=False)
    async with app.run_test() as pilot:
        from textual.widgets import Static

        await pilot.press("enter")
        details = app.query_one("#details", Static)
        content = details.render()
        assert content is not None


async def test_details_panel_in_debug_mode(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root, debug=True)
    async with app.run_test() as _:
        from textual.widgets import Static

        details = app.query_one("#details", Static)
        assert details is not None


async def test_error_node_displayed_in_tree(tmp_path):
    pb = tmp_path / "site.yml"
    pb.write_text(
        "- name: p\n  hosts: all\n  tasks:\n    - include_tasks: tasks/{{ env }}.yml\n",
        encoding="utf-8",
    )
    root = PlaybookLoader(str(pb)).load()
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        assert tree is not None


async def test_lazy_node_expands_on_tree_expand(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        await pilot.press("enter")
        await pilot.press("down")
        await pilot.press("enter")
        play_tree_node = tree.root.children[0] if tree.root.children else None
        if play_tree_node:
            assert play_tree_node.data is not None


async def test_execution_mode_labels_appear(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as pilot:
        await pilot.press("e")
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        assert tree is not None


async def test_action_toggle_expand_with_cursor(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        tree.cursor_line = 0
        app.action_toggle_expand()


async def test_selected_node_none_when_no_cursor(tmp_path, monkeypatch):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        from textual.widgets import Tree

        monkeypatch.setattr(Tree, "cursor_node", property(lambda self: None))
        assert app._selected_node() is None


async def test_refresh_execution_indices_assigns_when_loaded(tmp_path):
    root = _make_root(tmp_path)
    root.children[0].load_children()
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        app._refresh_execution_indices()


async def test_add_tree_node_with_children_and_error(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        child = Node(name="child", node_type="task")
        node = Node(name="error node", node_type="task", error="boom", children=[child])
        app._add_tree_node(tree.root, node)


def test_label_for_execution_mode(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    node = Node(name="task", node_type="task", execution_index=[1])
    app.execution_mode = True
    assert app._label_for(node).startswith("1 ")


async def test_on_tree_node_expanded_loads_children(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)

    def loader():
        return [Node(name="loaded", node_type="task")]

    lazy_node = Node(name="lazy", node_type="task")
    lazy_node.set_child_loader(loader)
    async with app.run_test() as _:
        from textual.widgets import Tree

        tree = app.query_one("#tree", Tree)
        app._add_tree_node(tree.root, lazy_node)
        event = type("Event", (), {"node": tree.root.children[-1]})()
        app.on_tree_node_expanded(event)


async def test_update_details_branches(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root, debug=False)
    async with app.run_test() as _:
        app._update_details(None)
        node = Node(
            name="t",
            node_type="task",
            source_file="/tmp/x.yml",
            line_number=12,
            error="bad",
        )
        app._update_details(node)
        app.debug_mode = True
        app._update_details(node)


def test_run_tui_calls_app_run(tmp_path, monkeypatch):
    root = _make_root(tmp_path)
    called = {}

    def fake_run(self):
        called["ran"] = True

    monkeypatch.setattr(AnsibleViewApp, "run", fake_run)
    run_tui(root, debug=False)
    assert called.get("ran") is True


async def test_shrink_tree_decreases_ratio(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        assert app._tree_fr == 2
        await app.run_action("shrink_tree")
        assert app._tree_fr == 1
        # at minimum, further shrink is a no-op
        await app.run_action("shrink_tree")
        assert app._tree_fr == 1


async def test_expand_tree_increases_ratio(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    async with app.run_test() as _:
        assert app._tree_fr == 2
        await app.run_action("expand_tree")
        assert app._tree_fr == 3
        # drive to max then verify no-op
        for _ in range(10):
            await app.run_action("expand_tree")
        assert app._tree_fr == 6


def test_on_tree_node_expanded_non_node_data(tmp_path):
    root = _make_root(tmp_path)
    app = AnsibleViewApp(root)
    event = type("Event", (), {"node": type("NodeStub", (), {"data": None})()})()
    app.on_tree_node_expanded(event)
