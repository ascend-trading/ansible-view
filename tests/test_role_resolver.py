from ansible_view.resolver.context import AnsibleConfig
from ansible_view.resolver.role_resolver import RoleResolver, _role_candidates

# _role_candidates tests


def test_role_candidates_with_explicit_collection():
    candidates = _role_candidates(
        "myrole",
        collections_paths=["/collections"],
        collection="mynamespace.mycol",
    )
    assert len(candidates) == 1
    assert "ansible_collections/mynamespace/mycol/roles/myrole" in candidates[0]


def test_role_candidates_collection_no_dot_returns_empty():
    candidates = _role_candidates(
        "myrole",
        collections_paths=["/collections"],
        collection="nodothere",
    )
    assert candidates == []


def test_role_candidates_fqcn_role_name():
    candidates = _role_candidates(
        "mynamespace.mycol.myrole",
        collections_paths=["/collections"],
        collection=None,
    )
    assert len(candidates) == 1
    assert "ansible_collections/mynamespace/mycol/roles/myrole" in candidates[0]


def test_role_candidates_dotted_name_fewer_than_three_parts():
    candidates = _role_candidates(
        "namespace.role",
        collections_paths=["/collections"],
        collection=None,
    )
    assert candidates == []


def test_role_candidates_plain_name_no_collection():
    candidates = _role_candidates("nginx", collections_paths=["/c"], collection=None)
    assert candidates == []


# RoleResolver tests


def _make_resolver(roles_path=None, collections_paths=None, task_loader=None):
    config = AnsibleConfig(
        config_path=None,
        roles_path=roles_path or [],
        collections_paths=collections_paths or [],
    )
    return RoleResolver(config, task_loader or (lambda p: []))


def test_build_role_node_not_found_sets_error(tmp_path):
    resolver = _make_resolver(roles_path=[str(tmp_path / "roles")])
    node = resolver.build_role_node("missing_role", source_file=None, line_number=None)
    assert node.error == "role not found in configured role_paths"


def test_build_role_node_found_has_no_error(tmp_path):
    role_dir = tmp_path / "roles" / "nginx" / "tasks"
    role_dir.mkdir(parents=True)
    (role_dir / "main.yml").write_text("- name: install\n  debug:\n    msg: hi\n")
    resolver = _make_resolver(roles_path=[str(tmp_path / "roles")])
    node = resolver.build_role_node("nginx", source_file=None, line_number=None)
    assert node.error is None
    assert node.has_lazy_children()


def test_build_role_node_tasks_file_missing_produces_error(tmp_path):
    role_dir = tmp_path / "roles" / "brokenrole"
    role_dir.mkdir(parents=True)
    (role_dir / "tasks").mkdir()
    resolver = _make_resolver(roles_path=[str(tmp_path / "roles")])
    node = resolver.build_role_node("brokenrole", source_file=None, line_number=None)
    node.load_children()
    tasks_node = node.children[0]
    assert tasks_node.error is not None
    assert "file not found" in tasks_node.error


def test_build_role_node_with_handlers(tmp_path):
    role_dir = tmp_path / "roles" / "webserver"
    (role_dir / "tasks").mkdir(parents=True)
    (role_dir / "handlers").mkdir(parents=True)
    (role_dir / "tasks" / "main.yml").write_text("- name: install\n  debug:\n    msg: hi\n")
    (role_dir / "handlers" / "main.yml").write_text(
        "- name: restart nginx\n  service:\n    name: nginx\n    state: restarted\n"
    )
    resolver = _make_resolver(roles_path=[str(tmp_path / "roles")])
    node = resolver.build_role_node("webserver", source_file=None, line_number=None)
    node.load_children()
    child_names = [c.name for c in node.children]
    assert "tasks/main.yml" in child_names
    assert "handlers/main.yml" in child_names


def test_build_role_node_tasks_from(tmp_path):
    role_dir = tmp_path / "roles" / "nginx"
    (role_dir / "tasks").mkdir(parents=True)
    (role_dir / "tasks" / "install.yml").write_text(
        "- name: install step\n  debug:\n    msg: install\n"
    )
    resolver = _make_resolver(roles_path=[str(tmp_path / "roles")])
    node = resolver.build_role_node(
        "nginx", source_file=None, line_number=None, tasks_from="install.yml"
    )
    node.load_children()
    assert node.children[0].name == "tasks/install.yml"


def test_build_role_node_via_collection_path(tmp_path):
    col_role_dir = (
        tmp_path
        / "collections"
        / "ansible_collections"
        / "myns"
        / "mycol"
        / "roles"
        / "myrole"
        / "tasks"
    )
    col_role_dir.mkdir(parents=True)
    (col_role_dir / "main.yml").write_text("- name: col task\n  debug:\n    msg: hi\n")
    resolver = _make_resolver(collections_paths=[str(tmp_path / "collections")])
    node = resolver.build_role_node(
        "myrole",
        source_file=None,
        line_number=None,
        collection="myns.mycol",
    )
    assert node.error is None
    assert node.has_lazy_children()
