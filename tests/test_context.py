import os

from ansible_view.resolver import context


def test_load_ansible_config_defaults_to_base_roles(tmp_path, monkeypatch):
    monkeypatch.delenv("ANSIBLE_CONFIG", raising=False)
    monkeypatch.delenv("ANSIBLE_ROLES_PATH", raising=False)
    monkeypatch.delenv("ANSIBLE_COLLECTIONS_PATHS", raising=False)
    monkeypatch.setattr(context, "_load_from_ansible_core", lambda base_dir: None)

    cfg = context.load_ansible_config(str(tmp_path))

    assert str(tmp_path / "roles") in cfg.roles_path


def test_load_ansible_config_reads_roles_path_from_cfg(tmp_path, monkeypatch):
    cfg_path = tmp_path / "ansible.cfg"
    role_one = tmp_path / "role_one"
    role_two = tmp_path / "role_two"
    cfg_path.write_text(
        "[defaults]\nroles_path = {0}{1}{2}\n".format(role_one, os.pathsep, role_two),
        encoding="utf-8",
    )

    monkeypatch.delenv("ANSIBLE_CONFIG", raising=False)
    monkeypatch.delenv("ANSIBLE_ROLES_PATH", raising=False)
    monkeypatch.setattr(context, "_load_from_ansible_core", lambda base_dir: None)

    cfg = context.load_ansible_config(str(tmp_path))

    assert str(tmp_path / "roles") in cfg.roles_path
    assert str(role_one) in cfg.roles_path
    assert str(role_two) in cfg.roles_path


def test_env_roles_path_overrides_cfg(tmp_path, monkeypatch):
    cfg_path = tmp_path / "ansible.cfg"
    cfg_path.write_text("[defaults]\nroles_path = /cfg/roles\n", encoding="utf-8")

    monkeypatch.setenv("ANSIBLE_ROLES_PATH", os.pathsep.join(["/env/roles"]))
    monkeypatch.delenv("ANSIBLE_CONFIG", raising=False)
    monkeypatch.setattr(context, "_load_from_ansible_core", lambda base_dir: None)

    cfg = context.load_ansible_config(str(tmp_path))

    assert "/env/roles" in cfg.roles_path
    assert "/cfg/roles" not in cfg.roles_path
