from __future__ import annotations

from typing import Any

import yaml


class LineNumberingLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        mapping.setdefault("__line__", node.start_mark.line + 1)
        return mapping


def load_yaml_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.load(handle, Loader=LineNumberingLoader)


def get_line_number(obj: Any) -> int | None:
    if isinstance(obj, dict):
        return obj.get("__line__")
    return None
