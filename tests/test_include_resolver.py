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


def test_resolve_prefers_parent_relative_when_exists(tmp_path):
    # File exists relative to parent → should be returned over base_dir candidate.
    parent_dir = tmp_path / "roles" / "myrole" / "tasks"
    parent_dir.mkdir(parents=True)
    role_file = parent_dir / "setup.yml"
    role_file.write_text("# role task", encoding="utf-8")
    # Also create a same-named file at base_dir level (should NOT be picked).
    (tmp_path / "setup.yml").write_text("# base task", encoding="utf-8")

    result = resolve_include_path(
        "setup.yml",
        parent_file=str(parent_dir / "main.yml"),
        base_dir=str(tmp_path),
    )
    assert result == str(role_file)


def test_resolve_falls_back_to_base_dir(tmp_path):
    # File does NOT exist relative to parent but DOES exist at base_dir.
    parent_dir = tmp_path / "roles" / "myrole" / "tasks"
    parent_dir.mkdir(parents=True)
    base_file = tmp_path / "tasks" / "common.yml"
    base_file.parent.mkdir(parents=True)
    base_file.write_text("# base task", encoding="utf-8")

    result = resolve_include_path(
        "tasks/common.yml",
        parent_file=str(parent_dir / "main.yml"),
        base_dir=str(tmp_path),
    )
    assert result == str(base_file)


def test_resolve_neither_exists_returns_parent_relative(tmp_path):
    # Neither path exists → return the parent-relative candidate so caller
    # can surface a meaningful "file not found" error.
    parent_dir = tmp_path / "plays"
    parent_dir.mkdir()
    result = resolve_include_path(
        "missing.yml",
        parent_file=str(parent_dir / "site.yml"),
        base_dir=str(tmp_path),
    )
    assert result == str(parent_dir / "missing.yml")
