"""
Core search functionality implementation.
"""
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import os
import fnmatch
import platform
import re
import json
from rich.console import Console
from rich.syntax import Syntax
from thefuzz import fuzz
from .optimizations import SearchOptimizer
from .config import Config

def process_batch(batch, pattern, search_path, params, config, format_size):
    """Process a batch of directory entries."""
    results = []
    for root, dirs, files in batch:
        # Early pruning of excluded directories
        dirs[:] = [d for d in dirs if not any(
            excl in str(Path(root) / d)
            for excl in config.get("default_excludes", [])
        )]
        
        if params.get("dirs_only"):
            for dir_name in dirs:
                if pattern.lower() in dir_name.lower():
                    dir_path = Path(root) / dir_name
                    try:
                        relative_path = dir_path.relative_to(search_path)
                        stat = dir_path.stat()
                        results.append({
                            "path": str(relative_path),
                            "size": "DIR",
                            "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                                config.get("date_format", "%Y-%m-%d %H:%M")
                            ),
                            "type": "directory"
                        })
                    except (ValueError, OSError):
                        continue
        else:
            for file in files:
                # Quick pattern check before more expensive operations
                if pattern == "*" or pattern.lower() in file.lower():
                    file_path = Path(root) / file
                    try:
                        relative_path = file_path.relative_to(search_path)
                        stat = file_path.stat()
                        results.append({
                            "path": str(relative_path),
                            "size": format_size(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                                config.get("date_format", "%Y-%m-%d %H:%M")
                            ),
                            "type": "file"
                        })
                    except (ValueError, OSError):
                        continue
    return results

class SearchTool:
    def __init__(self):
        self.DEFAULT_EXCLUDES = ['node_modules', '.build', 'dist', '.next', '__pycache__', '.git']
        self.results = []
        self.console = Console()
        self.is_windows = platform.system() == "Windows"
        self.config = Config()
        self.optimizer = SearchOptimizer(self.config.config)
        
    def parse_size(self, size_str: str) -> int:
        """Convert human-readable size to bytes"""
        if not size_str:
            return 0
        units = {'K': 1024, 'M': 1024**2, 'G': 1024**3}
        size_str = size_str.upper()
        if size_str[-1] in units:
            return int(float(size_str[:-1]) * units[size_str[-1]])
        return int(size_str)

    def format_size(self, size: int) -> str:
        """Convert bytes to human-readable size"""
        for unit in ['B', 'K', 'M', 'G']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}T"

    def fuzzy_match(self, text: str, pattern: str) -> bool:
        """Perform fuzzy matching on text"""
        # First try exact pattern matching
        if fnmatch.fnmatch(text.lower(), pattern.lower()):
            return True
            
        # If that fails, try fuzzy matching
        if pattern.startswith("~"):  # Explicit fuzzy search with ~ prefix
            pattern = pattern[1:]
            ratio = fuzz.partial_ratio(pattern.lower(), text.lower())
            return ratio >= self.config.get("fuzzy_threshold", 65)
            
        return False

    def search_content(self, file_path: Path, pattern: str) -> bool:
        """Search file content for pattern"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if pattern.startswith("~"):  # Fuzzy search in content
                    pattern = pattern[1:]
                    return fuzz.partial_ratio(pattern.lower(), content.lower()) >= self.config.get("fuzzy_threshold", 65)
                return bool(re.search(pattern, content, re.IGNORECASE))
        except:
            return False

    def preview_file(self, file_path: Path) -> str:
        """Generate a preview of the file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(self.config.get("preview_length", 1000))
                syntax = Syntax(
                    content, 
                    file_path.suffix[1:] if file_path.suffix else "txt",
                    theme=self.config.get("theme", "monokai")
                )
                return syntax
        except:
            return "[red]Unable to preview file[/red]"

    def should_include_file(self, file_path: Path, params: dict) -> bool:
        """Check if file should be included based on filters"""
        # For directory-only search
        if params.get("dirs_only", False):
            return file_path.is_dir()

        # Check if it's a file for normal searches
        if not file_path.is_file():
            return False

        # Check extensions
        if params["extensions"] and not any(file_path.name.endswith(ext) for ext in params["extensions"]):
            return False

        # Check size
        try:
            size = os.path.getsize(file_path)
            if params["min_size"] and size < self.parse_size(params["min_size"]):
                return False
            if params["max_size"] and size > self.parse_size(params["max_size"]):
                return False
        except OSError:
            return False

        # Check exclude patterns
        exclude_patterns = params["exclude"] + self.config.get("default_excludes", self.DEFAULT_EXCLUDES)
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(str(file_path), pattern):
                return False

        # Check content if specified
        if params.get("content_pattern"):
            if not self.search_content(file_path, params["content_pattern"]):
                return False

        return True

    def search(self, params: dict):
        """Execute the search based on user parameters"""
        import select
        import sys
        import msvcrt if sys.platform == "win32" else termios
        import tty
        from itertools import islice
        
        def is_enter_pressed():
            if sys.platform == "win32":
                # Windows implementation
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    return key == b'\r'
                return False
            else:
                # Unix implementation
                if select.select([sys.stdin], [], [], 0)[0]:
                    return sys.stdin.read(1) == '\n'
                return False
            
        # Save terminal settings on Unix systems
        if sys.platform != "win32":
            old_settings = termios.tcgetattr(sys.stdin)
            
        try:
            # Set terminal to raw mode on Unix systems
            if sys.platform != "win32":
                tty.setraw(sys.stdin.fileno())
            
            self.results = []
            search_path = Path(params["path"])
            pattern = params["pattern"]
            max_results = self.config.get("max_results", 1000)
            
            # Debug output
            self.console.print(f"\n[dim]Searching in: {search_path}[/dim]")
            self.console.print(f"[dim]Pattern: {pattern}[/dim]")
            self.console.print("[dim]Press Enter to stop search and show results...[/dim]\n")
            
            # Initialize params with defaults
            params.setdefault("extensions", [])
            params.setdefault("min_size", None)
            params.setdefault("max_size", None)
            params.setdefault("exclude", [])
            
            search_stopped = False
            
            if params.get("dirs_only"):
                # Optimized directory search
                for root, dirs, _ in os.walk(search_path):
                    if search_stopped or len(self.results) >= max_results:
                        break
                        
                    if is_enter_pressed():
                        search_stopped = True
                        break
                        
                    # Skip excluded directories early
                    root_path = Path(root)
                    if any(excl in str(root_path).split(os.sep) for excl in self.config.get("default_excludes", self.DEFAULT_EXCLUDES)):
                        continue
                    
                    # Filter dirs list in-place to skip excluded ones
                    dirs[:] = [d for d in dirs if not any(
                        excl in str(Path(root) / d)
                        for excl in self.config.get("default_excludes", self.DEFAULT_EXCLUDES)
                    )]
                    
                    for dir_name in dirs:
                        if pattern == "*" or pattern[1:-1].lower() in dir_name.lower():
                            dir_path = root_path / dir_name
                            try:
                                relative_path = dir_path.relative_to(search_path)
                                stat = dir_path.stat()
                                result = {
                                    "path": str(relative_path),
                                    "size": "DIR",
                                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                                        self.config.get("date_format", "%Y-%m-%d %H:%M")
                                    ),
                                    "type": "directory"
                                }
                                self.results.append(result)
                                self.console.print(f"[green]Found:[/green] {relative_path}")
                                
                                if len(self.results) >= max_results:
                                    break
                            except (ValueError, OSError):
                                continue
            else:
                # File search
                for root, _, files in os.walk(search_path):
                    if search_stopped or len(self.results) >= max_results:
                        break
                        
                    if is_enter_pressed():
                        search_stopped = True
                        break
                        
                    root_path = Path(root)
                    if any(excl in str(root_path).split(os.sep) for excl in self.config.get("default_excludes", self.DEFAULT_EXCLUDES)):
                        continue
                        
                    for file in files:
                        if pattern == "*" or pattern[1:-1].lower() in file.lower():
                            file_path = root_path / file
                            if self.should_include_file(file_path, params):
                                try:
                                    relative_path = file_path.relative_to(search_path)
                                    stat = file_path.stat()
                                    result = {
                                        "path": str(relative_path),
                                        "size": self.format_size(stat.st_size),
                                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                                            self.config.get("date_format", "%Y-%m-%d %H:%M")
                                        ),
                                        "type": "file"
                                    }
                                    self.results.append(result)
                                    self.console.print(f"[green]Found:[/green] {relative_path}")
                                    
                                    if len(self.results) >= max_results:
                                        break
                                except (ValueError, OSError):
                                    continue
            
            if search_stopped:
                self.console.print("\n[yellow]Search stopped by user[/yellow]")
            elif len(self.results) >= max_results:
                self.console.print("\n[yellow]Maximum results limit reached[/yellow]")
                
            # Sort results
            sort_key = params.get("sort_by", self.config.get("sort_by", "path"))
            reverse = params.get("sort_reverse", self.config.get("sort_reverse", False))
            self.results.sort(key=lambda x: x[sort_key], reverse=reverse)
            
            # Add previews if requested (only for the first few results to keep it fast)
            if params.get("preview", self.config.get("show_preview", True)):
                for result in islice(self.results, 10):  # Only preview first 10 results
                    if result["type"] == "file":
                        result["preview"] = self.preview_file(Path(search_path) / result["path"])
                        
            self.console.print(f"\n[dim]Found {len(self.results)} results[/dim]")
            
        finally:
            # Restore terminal settings on Unix systems
            if sys.platform != "win32":
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def _search_directories(self, pattern: str, path: Path) -> List[dict]:
        """Optimized directory search"""
        results = []
        pattern = pattern.rstrip('/')  # Remove trailing slash if present
        
        # Debug output for directory search
        self.console.print(f"[dim]Looking for directories matching: {pattern}[/dim]")
        
        for root, dirs, _ in os.walk(path):
            root_path = Path(root)
            
            # Skip excluded directories
            if any(excl in str(root_path).split(os.sep) for excl in self.config.get("default_excludes", self.DEFAULT_EXCLUDES)):
                continue
                
            for dir_name in dirs:
                # Simple name matching first
                if pattern.lower() in dir_name.lower():
                    dir_path = root_path / dir_name
                    try:
                        relative_path = dir_path.relative_to(path)
                        # Skip if path matches any exclude pattern
                        if any(fnmatch.fnmatch(str(relative_path), excl) for excl in self.config.get("default_excludes", self.DEFAULT_EXCLUDES)):
                            continue
                            
                        try:
                            stat = dir_path.stat()
                            results.append({
                                "path": str(relative_path),
                                "size": "DIR",
                                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                                    self.config.get("date_format", "%Y-%m-%d %H:%M")
                                ),
                                "type": "directory"
                            })
                            # Debug output for found directory
                            self.console.print(f"[dim]Found directory: {relative_path}[/dim]")
                        except OSError:
                            continue
                    except ValueError:
                        continue
                    
        if not results:
            self.console.print("[yellow]No directories found matching the pattern[/yellow]")
            
        return results

