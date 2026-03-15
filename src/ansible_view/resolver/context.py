from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AnsibleConfig:
    config_path: Optional[str]
    roles_path: List[str]
    collections_paths: List[str]


def _split_paths(value: str) -> List[str]:
    return [os.path.expanduser(path.strip()) for path in value.split(os.pathsep) if path.strip()]


def _read_config(path: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(path)
    return config


def load_ansible_config(base_dir: str) -> AnsibleConfig:
    ansible_config = _load_from_ansible_core(base_dir)
    if ansible_config:
        return ansible_config

    env_config = os.environ.get("ANSIBLE_CONFIG")
    candidates = [
        env_config,
        os.path.join(base_dir, "ansible.cfg"),
        os.path.expanduser("~/.ansible.cfg"),
        "/etc/ansible/ansible.cfg",
    ]
    config_path = next((c for c in candidates if c and os.path.exists(c)), None)
    config = _read_config(config_path) if config_path else configparser.ConfigParser()

    roles_path_value = os.environ.get("ANSIBLE_ROLES_PATH")
    if not roles_path_value:
        roles_path_value = config.get("defaults", "roles_path", fallback="")
    roles_path = _split_paths(roles_path_value) if roles_path_value else []

    collections_value = os.environ.get("ANSIBLE_COLLECTIONS_PATHS")
    if not collections_value:
        collections_value = config.get("defaults", "collections_paths", fallback="")
    if not collections_value:
        collections_value = config.get("defaults", "collections_path", fallback="")
    collections_paths = _split_paths(collections_value) if collections_value else []

    # Defaults modeled after ansible-core defaults.
    if not roles_path:
        roles_path = [
            os.path.join(base_dir, "roles"),
            os.path.expanduser("~/.ansible/roles"),
            "/etc/ansible/roles",
        ]
    else:
        # Ensure playbook-local roles are searched first.
        roles_path = [os.path.join(base_dir, "roles")] + roles_path

    if not collections_paths:
        collections_paths = [
            os.path.expanduser("~/.ansible/collections"),
            "/usr/share/ansible/collections",
        ]

    return AnsibleConfig(
        config_path=config_path,
        roles_path=roles_path,
        collections_paths=collections_paths,
    )


def _load_from_ansible_core(base_dir: str) -> Optional[AnsibleConfig]:
    try:
        from ansible.config.manager import ConfigManager
    except Exception:
        return None

    try:
        manager = ConfigManager()
        config_path = getattr(manager, "config_file", None)
        roles_value = manager.get_config_value("DEFAULT_ROLES_PATH")
        collections_value = manager.get_config_value("COLLECTIONS_PATHS")
        if not collections_value:
            collections_value = manager.get_config_value("COLLECTIONS_PATH")
        roles_path = _split_paths(roles_value) if roles_value else []
        collections_paths = _split_paths(collections_value) if collections_value else []
        if not roles_path:
            roles_path = [os.path.join(base_dir, "roles")]
        else:
            roles_path = [os.path.join(base_dir, "roles")] + roles_path
        if not collections_paths:
            collections_paths = [
                os.path.expanduser("~/.ansible/collections"),
                "/usr/share/ansible/collections",
            ]
        return AnsibleConfig(
            config_path=config_path,
            roles_path=roles_path,
            collections_paths=collections_paths,
        )
    except Exception:
        return None
