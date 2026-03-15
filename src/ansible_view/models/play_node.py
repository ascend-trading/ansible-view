from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .node import Node


@dataclass
class PlayNode(Node):
    name: str
    node_type: str = "play"
    source_file: Optional[str] = None
    line_number: Optional[int] = None
