from ansible_view.resolver.include_resolver import resolve_include_path


def test_resolve_absolute_path(tmp_path):
    absolute = str(tmp_path / "play.yml")
    assert resolve_include_path(absolute, parent_file=None, base_dir=str(tmp_path)) == absolute


def test_resolve_dynamic_path_returns_none(tmp_path):
    assert resolve_include_path("{{ dynamic }}", parent_file=None, base_dir=str(tmp_path)) is None


def test_resolve_relative_path_with_parent(tmp_path):
    parent = tmp_path / "dir" / "main.yml"
    expected = str(tmp_path / "dir" / "tasks" / "setup.yml")
    result = resolve_include_path(
        "tasks/setup.yml", parent_file=str(parent), base_dir=str(tmp_path)
    )
    assert result == expected


def test_resolve_relative_path_without_parent(tmp_path):
    expected = str(tmp_path / "tasks" / "setup.yml")
    result = resolve_include_path("tasks/setup.yml", parent_file=None, base_dir=str(tmp_path))
    assert result == expected
