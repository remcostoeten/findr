"""
User interface components using questionary.
"""
import questionary
from rich.console import Console
from rich.panel import Panel
from pathlib import Path

class UI:
    def __init__(self):
        self.console = Console()

    def prompt_user(self, config: dict) -> dict:
        """Collect user inputs through interactive prompts"""
        # [Previous implementation moved from SearchTool]
        pass

    def display_results(self, results: list):
        """Display search results in a formatted table"""
        # [Previous implementation moved from SearchTool]
        pass
