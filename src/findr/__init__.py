"""
Package initialization file. Exports main components and version.
"""
from .core import SearchTool
from .cli import main

__version__ = "0.1.0"
__all__ = ["SearchTool", "main"]
