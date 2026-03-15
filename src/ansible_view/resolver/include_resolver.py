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
    # Try relative to the including file first (covers role-internal includes).
    if parent_file:
        candidate = os.path.normpath(os.path.join(os.path.dirname(parent_file), include_path))
        if os.path.exists(candidate):
            return candidate
    # Fall back to the playbook root (covers paths like tasks/xxx.yml used
    # from inside a role when the file lives at the project root level).
    root_candidate = os.path.normpath(os.path.join(base_dir, include_path))
    if os.path.exists(root_candidate):
        return root_candidate
    # Neither exists — return the parent-relative path so the caller can
    # surface a "file not found" error with the most-likely intended path.
    if parent_file:
        return os.path.normpath(os.path.join(os.path.dirname(parent_file), include_path))
    return root_candidate
