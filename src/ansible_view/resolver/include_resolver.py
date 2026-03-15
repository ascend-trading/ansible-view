from __future__ import annotations

import os
from typing import Optional


def resolve_include_path(
    include_path: str, parent_file: Optional[str], base_dir: str
) -> Optional[str]:
    if "{{" in include_path or "}}" in include_path:
        return None
    if os.path.isabs(include_path):
        return include_path
    if parent_file:
        return os.path.normpath(os.path.join(os.path.dirname(parent_file), include_path))
    return os.path.normpath(os.path.join(base_dir, include_path))
