from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .node import Node


@dataclass
class TaskNode(Node):
    name: str
    node_type: str = "task"
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    module: Optional[str] = None
    args: Optional[Dict] = None
    when_conditions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    register_variable: Optional[str] = None
    loop: Optional[str] = None
    notify: Optional[List[str]] = None
    variables: Optional[List[str]] = None
    error: Optional[str] = None
