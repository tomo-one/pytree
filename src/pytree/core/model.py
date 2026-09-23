"""Framework-agnostisches Datenmodell für den Scan-Baum.

Bewusst ohne jegliche Textual-/CLI-Abhängigkeit, damit eine spätere GUI
dieselben Klassen wiederverwenden kann.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ScanState(Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    DONE = "done"
    ERROR = "error"


@dataclass
class ScanIssue:
    path: Path
    message: str


@dataclass
class Node:
    path: Path
    name: str
    is_dir: bool
    is_symlink: bool = False
    size: int = 0
    file_count: int = 0
    children: list["Node"] | None = None
    state: ScanState = ScanState.PENDING
    error: str | None = None
    parent: "Node | None" = field(default=None, repr=False)

    @property
    def is_scanned(self) -> bool:
        return self.children is not None

    def percent_of_parent(self) -> float | None:
        if self.parent is None or not self.parent.size:
            return None
        return self.size / self.parent.size
