"""
User interface components using questionary.
"""
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from pathlib import Path
import sys

class UI:
    def __init__(self):
        self.console = Console()

    def show_help(self):
        """Display help information"""
        help_text = """
# Findr Help

## Basic Usage
- Use arrow keys (↑/↓) to navigate
- Press Enter to select
- Press Ctrl+C to exit at any time
- Press 'h' for this help menu
- Press 'q' to quit

## Search Patterns
- `*` matches any characters
- `?` matches single character
- `*.{ext1,ext2}` matches multiple extensions
- `**/pattern` matches in all subdirectories
- `test_*.py` matches files starting with 'test_'
- `*/` matches directories only

## Size Filters
- Use K, M, G for sizes (e.g., 500K, 10M, 1G)
- Ranges combine min and max sizes
- Common presets available

## Examples
- `*.py` - Find Python files
- `*test*` - Find files containing 'test'
- `src/*.{js,ts}` - Find JavaScript/TypeScript in src
- `**/*.md` - Find all Markdown files recursively
- `>10M` - Find files larger than 10MB

## Tips
- Use directory search for faster navigation
- Combine patterns with size filters
- Exclude patterns to skip unwanted files
- Search history is saved automatically
"""
        md = Markdown(help_text)
        self.console.print(Panel(md, title="[bold cyan]Findr Help[/bold cyan]", border_style="cyan"))
        input("\nPress Enter to continue...")

    def show_welcome(self):
        """Display welcome message"""
        welcome = Panel(
            "[bold cyan]Welcome to Findr![/bold cyan]\n\n"
            "🔍 Interactive file search tool\n"
            "Press [bold yellow]'h'[/bold yellow] for help or [bold yellow]'q'[/bold yellow] to quit\n"
            "Use [bold yellow]arrow keys[/bold yellow] to navigate and [bold yellow]Enter[/bold yellow] to select",
            title="[bold green]Findr[/bold green]",
            border_style="green"
        )
        self.console.print(welcome)

    def prompt_user(self, config: dict, skip_intro: bool = False, initial_params: dict = None) -> dict:
        """Collect user inputs through interactive prompts"""
        if not skip_intro:
            self.show_welcome()
            while True:
                key = self.console.input("\n[cyan]Press h for help, q to quit, or Enter to continue: [/cyan]")
                if key.lower() == 'h':
                    self.show_help()
                    continue
                elif key.lower() == 'q':
                    sys.exit(0)
                elif key:
                    continue
                break

        # Start with root directory selection
        self.console.print("\n[bold cyan]Directory Selection[/bold cyan]")
        default_path = initial_params.get("path", str(Path.cwd())) if initial_params else str(Path.cwd())
        search_path = questionary.path(
            "Enter the directory to search in:",
            default=default_path,
            validate=lambda x: Path(x).exists(),
            style=questionary.Style([
                ('question', 'fg:cyan bold'),
                ('path', 'fg:green'),
                ('selected', 'fg:white bg:blue')
            ])
        ).ask()

        # If using a preset, confirm or modify the preset settings
        if initial_params:
            use_preset_settings = questionary.confirm(
                "Use preset settings?",
                default=True
            ).ask()
            
            if use_preset_settings:
                params = initial_params.copy()
                params["path"] = search_path
                return params

        # Show search pattern selection
        self.console.print("\n[bold cyan]Search Pattern Selection[/bold cyan]")
        
        # First ask for the type of search
        search_type = questionary.select(
            "What type of search?",
            choices=[
                "🔍 Find files by name",
                "📝 Find text inside files",
                "📁 Find folders only",
                "🎯 Find files by type (*.py, *.js, etc)",
                "✨ Custom search pattern"
            ]
        ).ask()

        if search_type == "📁 Find folders only":
            folder_name = questionary.text(
                "Enter folder name to find:",
                instruction="Enter name or pattern (e.g., 'findr', '*test*', 'src*', '*lib')"
            ).ask()
            # If no wildcards are used, wrap with * for convenience
            pattern = f"*{folder_name}*" if not any(c in folder_name for c in "*?[{") else folder_name
            params = {
                "path": search_path,
                "pattern": pattern,
                "dirs_only": True,
                "preview": False,
                "exclude": config.get("default_excludes", [])
            }
            
        elif search_type == "🔍 Find files by name":
            name_pattern = questionary.text(
                "Enter file name pattern:",
                instruction="e.g., 'config' finds files containing 'config', '*.txt' finds .txt files"
            ).ask()
            pattern = f"*{name_pattern}*" if not any(c in name_pattern for c in "*?[{") else name_pattern
            params = {
                "path": search_path,
                "pattern": pattern,
                "dirs_only": False,
                "preview": config.get("show_preview", True),
                "exclude": config.get("default_excludes", [])
            }
            
        elif search_type == "📝 Find text inside files":
            content_pattern = questionary.text(
                "Enter text to search for inside files:",
                instruction="Enter the text or regex pattern to find"
            ).ask()
            
            file_pattern = questionary.text(
                "Search in which files? (optional)",
                default="*",
                instruction="e.g., '*.py' for Python files, '*.{js,ts}' for JS/TS, or just Enter for all files"
            ).ask()
            
            params = {
                "path": search_path,
                "pattern": file_pattern,
                "content_pattern": content_pattern,
                "dirs_only": False,
                "preview": True,  # Always show preview for content search
                "exclude": config.get("default_excludes", [])
            }
            
        elif search_type == "🎯 Find files by type":
            file_type = questionary.select(
                "Which type of files?",
                choices=[
                    "🐍 Python files (*.py)",
                    "📜 JavaScript files (*.js, *.jsx)",
                    "📘 TypeScript files (*.ts, *.tsx)",
                    "🌐 Web files (*.html, *.css)",
                    "⚙️ Config files (*.json, *.yaml, etc)",
                    "📝 Documentation (*.md, *.txt)",
                    "🖼️ Images (*.jpg, *.png, etc)",
                    "🎵 Media files (*.mp3, *.mp4, etc)",
                    "📦 Archive files (*.zip, *.tar, etc)"
                ]
            ).ask()

            # Map selections to patterns
            pattern_map = {
                "🐍 Python files (*.py)": "*.py",
                "📜 JavaScript files (*.js, *.jsx)": "*.{js,jsx}",
                "📘 TypeScript files (*.ts, *.tsx)": "*.{ts,tsx}",
                "🌐 Web files (*.html, *.css)": "*.{html,css,scss,sass}",
                "⚙️ Config files (*.json, *.yaml, etc)": "*.{json,yaml,yml,toml,ini,conf}",
                "📝 Documentation (*.md, *.txt)": "*.{md,mdx,rst,txt}",
                "🖼️ Images (*.jpg, *.png, etc)": "*.{jpg,jpeg,png,gif,svg,webp}",
                "🎵 Media files (*.mp3, *.mp4, etc)": "*.{mp3,mp4,wav,avi,mkv}",
                "📦 Archive files (*.zip, *.tar, etc)": "*.{zip,tar,gz,7z,rar}"
            }
            pattern = pattern_map[file_type]
            params = {
                "path": search_path,
                "pattern": pattern,
                "dirs_only": False,
                "preview": config.get("show_preview", True),
                "exclude": config.get("default_excludes", [])
            }
            
        else:  # Custom search pattern
            self.console.print("\n[cyan]Search Pattern Help:[/cyan]")
            self.console.print("- [yellow]*.txt[/yellow] finds all .txt files")
            self.console.print("- [yellow]*test*[/yellow] finds files containing 'test'")
            self.console.print("- [yellow]*.{js,ts}[/yellow] finds .js and .ts files")
            self.console.print("- [yellow]src/*.py[/yellow] finds Python files in src directory")
            pattern = questionary.text(
                "Enter custom search pattern:",
                instruction="Enter your search pattern using wildcards"
            ).ask()
            params = {
                "path": search_path,
                "pattern": pattern,
                "dirs_only": pattern.endswith('/'),
                "preview": config.get("show_preview", True),
                "exclude": config.get("default_excludes", [])
            }

        # Ask about additional filters
        use_filters = questionary.confirm(
            "Would you like to use additional filters?",
            default=False
        ).ask()

        if use_filters:
            self.console.print("\n[bold cyan]Filter Configuration[/bold cyan]")
            if not params["dirs_only"]:
                if not params["extensions"]:
                    extensions = questionary.text(
                        "Enter file extensions to filter (comma-separated, e.g., py,js,txt):",
                        instruction="Leave empty to skip"
                    ).ask()
                    if extensions:
                        params["extensions"] = [f".{ext.strip()}" for ext in extensions.split(",")]

                if not (params["min_size"] or params["max_size"]):
                    size_choice = questionary.select(
                        "Filter by file size?",
                        choices=[
                            "📊 No size filter",
                            "🔽 Small files (< 100KB)",
                            "➡️ Medium files (100KB - 10MB)",
                            "🔼 Large files (> 10MB)",
                            "⚖️ Custom size range"
                        ]
                    ).ask()

                    if "Small files" in size_choice:
                        params["max_size"] = "100K"
                    elif "Medium files" in size_choice:
                        params["min_size"] = "100K"
                        params["max_size"] = "10M"
                    elif "Large files" in size_choice:
                        params["min_size"] = "10M"
                    elif "Custom size range" in size_choice:
                        min_size = questionary.text(
                            "Enter minimum file size (e.g., 1M, 500K):",
                            instruction="Leave empty to skip"
                        ).ask()
                        if min_size:
                            params["min_size"] = min_size

                        max_size = questionary.text(
                            "Enter maximum file size (e.g., 10M, 1G):",
                            instruction="Leave empty to skip"
                        ).ask()
                        if max_size:
                            params["max_size"] = max_size

            if not params["exclude"]:
                exclude = questionary.text(
                    "Enter additional patterns to exclude (comma-separated):",
                    instruction="e.g., *.tmp,build/*"
                ).ask()
                if exclude:
                    params["exclude"].extend([pat.strip() for pat in exclude.split(",")])

            if not params["content_pattern"]:
                use_content_search = questionary.confirm(
                    "Would you like to search file contents?",
                    default=False
                ).ask()
                if use_content_search:
                    params["content_pattern"] = questionary.text(
                        "Enter content search pattern:",
                        instruction="Regular expression or text to search for"
                    ).ask()

        return params

    def display_results(self, results: list):
        """Display search results in a formatted table"""
        if not results:
            self.console.print("\n[yellow]No results found[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Path", style="cyan")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Modified", style="yellow")
        table.add_column("Type", style="blue")

        for result in results:
            table.add_row(
                result["path"],
                result["size"],
                result["modified"],
                result["type"]
            )

            if result.get("preview"):
                table.add_row(
                    Panel(result["preview"], border_style="dim"),
                    "", "", "",
                    style="dim"
                )

        self.console.print(table)
