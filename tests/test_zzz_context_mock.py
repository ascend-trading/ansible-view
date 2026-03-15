import sys
from unittest.mock import MagicMock, patch

from ansible_view.resolver.context import _load_from_ansible_core, load_ansible_config


def test_load_from_ansible_core_succeeds_with_mock():
    mock_manager = MagicMock()
    mock_manager.config_file = "/fake/ansible.cfg"
    mock_manager.get_config_value.side_effect = lambda key: {
        "DEFAULT_ROLES_PATH": "/fake/roles",
        "COLLECTIONS_PATHS": "",
        "COLLECTIONS_PATH": "/fake/collections",
    }.get(key, "")

    mock_cm_class = MagicMock(return_value=mock_manager)

    with patch.dict(
        sys.modules,
        {
            "ansible": MagicMock(),
            "ansible.config": MagicMock(),
            "ansible.config.manager": MagicMock(ConfigManager=mock_cm_class),
        },
    ):
        result = _load_from_ansible_core("/base")

    assert result is not None
    assert any("/fake/roles" in p for p in result.roles_path)


def test_load_ansible_config_returns_ansible_core_result_when_available():
    mock_manager = MagicMock()
    mock_manager.config_file = None
    mock_manager.get_config_value.return_value = ""

    mock_cm_class = MagicMock(return_value=mock_manager)

    with patch.dict(
        sys.modules,
        {
            "ansible": MagicMock(),
            "ansible.config": MagicMock(),
            "ansible.config.manager": MagicMock(ConfigManager=mock_cm_class),
        },
    ):
        config = load_ansible_config("/base")

    assert config is not None
    assert hasattr(config, "roles_path")


def test_load_from_ansible_core_configmanager_raises_returns_none():
    mock_cm_class = MagicMock(side_effect=RuntimeError("no config"))

    with patch.dict(
        sys.modules,
        {
            "ansible": MagicMock(),
            "ansible.config": MagicMock(),
            "ansible.config.manager": MagicMock(ConfigManager=mock_cm_class),
        },
    ):
        result = _load_from_ansible_core("/base")

    assert result is None
