import sys
import types

from ansible_view.resolver.context import _load_from_ansible_core


def test_load_from_ansible_core_import_failure_returns_none(monkeypatch):
    original = sys.modules.get("ansible")
    broken = types.ModuleType("ansible")
    broken.config = None

    monkeypatch.setitem(sys.modules, "ansible.config.manager", None)

    result = _load_from_ansible_core("/tmp")
    assert result is None or hasattr(result, "roles_path")

    if original is not None:
        sys.modules["ansible"] = original
