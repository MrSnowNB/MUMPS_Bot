"""Stage 4: Minimal Pydantic v2 IR models for MUMPS_Bot PoC."""
from __future__ import annotations
from pydantic.dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class IRNode:
    """Base for all IR nodes. Source provenance is mandatory."""
    node_id: str
    source_file: str
    source_line: int
    source_col: int
    raw_mumps: str

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())


@dataclass
class IRLabel(IRNode):
    """A MUMPS routine label / entry point."""
    name: str


@dataclass
class IRWrite(IRNode):
    """WRITE command — outputs a string or value."""
    argument: str
    has_newline: bool = False


@dataclass
class IRQuit(IRNode):
    """QUIT command — exits a routine or block."""
    return_value: Optional[str] = None


@dataclass
class IRRoutine(IRNode):
    """Top-level routine container."""
    name: str
    entry_points: list  # list of IRLabel
    body: list          # list of IRNode subclasses
