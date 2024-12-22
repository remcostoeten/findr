"""
Optimized search implementations for the Findr tool.
"""
from typing import List, Dict, Set
import os
from pathlib import Path
import platform
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from thefuzz import fuzz
import fnmatch

class SearchOptimizer:
    def __init__(self, config: dict):
        self.config = config
        self.is_windows = platform.system() == "Windows"
        self._file_cache: Dict[str, Set[str]] = {}
        self._content_cache: Dict[str, str] = {}
        
    def quick_file_search(self, pattern: str, path: Path) -> List[dict]:
        """Fast file search using OS-specific optimizations"""
        results = []
        max_results = self.config["max_results"]
        
        # Use cached file list if available
        cache_key = str(path)
        if cache_key not in self._file_cache:
            self._file_cache[cache_key] = set()
            # Build file list using OS-specific methods
            if self.is_windows:
                # Use Windows search API if available
                try:
                    import win32file
                    import win32con
                    results.extend(self._windows_file_search(pattern, path))
                except ImportError:
                    results.extend(self._fallback_file_search(pattern, path))
            else:
                # Use find/locate on Unix systems
                try:
                    results.extend(self._unix_file_search(pattern, path))
                except:
                    results.extend(self._fallback_file_search(pattern, path))
                    
        # Format results
        formatted_results = []
        for file_path in results[:max_results]:
            try:
                stat = Path(file_path).stat()
                formatted_results.append({
                    "path": str(Path(file_path).relative_to(path)),
                    "size": self._format_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        self.config["date_format"]
                    ),
                    "type": "file"
                })
            except OSError:
                continue
                
        return formatted_results
        
    def quick_content_search(self, pattern: str, path: Path) -> List[dict]:
        """Fast content search using parallel processing"""
        results = []
        max_results = self.config["max_results"]
        
        # Compile regex pattern
        try:
            regex = re.compile(pattern)
        except re.error:
            regex = re.compile(re.escape(pattern))
            
        # Use ThreadPoolExecutor for parallel search
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = []
            
            for root, _, files in os.walk(path):
                root_path = Path(root)
                
                # Skip excluded directories
                if any(excl in str(root_path).parts 
                      for excl in self.config["default_excludes"]):
                    continue
                    
                for file in files:
                    file_path = root_path / file
                    if len(results) >= max_results:
                        break
                        
                    # Skip large binary files
                    try:
                        if (file_path.stat().st_size > 
                            self.config["binary_size_limit"]):
                            continue
                    except OSError:
                        continue
                        
                    futures.append(
                        executor.submit(
                            self._search_file_content,
                            file_path,
                            regex,
                            path
                        )
                    )
                    
            # Collect results
            for future in futures:
                if result := future.result():
                    results.append(result)
                    if len(results) >= max_results:
                        break
                        
        return results
        
    def _windows_file_search(self, pattern: str, path: Path) -> List[str]:
        """Use Windows Search API for fast file search"""
        import win32file
        import win32con
        
        results = []
        handle = win32file.FindFirstFile(
            str(path / "**" / "*.*"),
            win32con.FILE_ATTRIBUTE_NORMAL
        )
        
        try:
            while True:
                data = win32file.FindNextFile(handle)
                if not data[0]:
                    break
                    
                file_name = data[8]
                if fuzz.ratio(file_name, pattern) >= self.config["fuzzy_threshold"]:
                    results.append(str(path / file_name))
        finally:
            win32file.FindClose(handle)
            
        return results
        
    def _unix_file_search(self, pattern: str, path: Path) -> List[str]:
        """Use find/locate commands for fast file search on Unix systems"""
        import subprocess
        
        results = []
        try:
            # Try using locate first (faster but requires updatedb)
            cmd = f"locate -r '{pattern}' | grep '^{path}'"
            output = subprocess.check_output(
                cmd, 
                shell=True, 
                text=True
            ).splitlines()
            results.extend(output)
        except:
            # Fall back to find
            cmd = f"find {path} -type f -name '*{pattern}*'"
            output = subprocess.check_output(
                cmd,
                shell=True,
                text=True
            ).splitlines()
            results.extend(output)
            
        return results
        
    def _fallback_file_search(self, pattern: str, path: Path) -> List[str]:
        """Standard file search implementation as fallback"""
        results = []
        
        for root, _, files in os.walk(path):
            root_path = Path(root)
            
            # Skip excluded directories
            if any(excl in str(root_path).split(os.sep) 
                  for excl in self.config.get("default_excludes", [])):
                continue
                
            for file in files:
                file_path = root_path / file
                try:
                    relative_path = file_path.relative_to(path)
                    if any(fnmatch.fnmatch(str(relative_path), excl) 
                          for excl in self.config.get("default_excludes", [])):
                        continue
                        
                    if fuzz.ratio(file, pattern) >= self.config.get("fuzzy_threshold", 65):
                        results.append({
                            "path": str(relative_path),
                            "size": self._format_size(file_path.stat().st_size),
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
                                self.config.get("date_format", "%Y-%m-%d %H:%M")
                            ),
                            "type": "file"
                        })
                except (ValueError, OSError):
                    continue
                    
        return results
        
    def _search_file_content(
        self, 
        file_path: Path, 
        pattern: re.Pattern, 
        base_path: Path
    ) -> Dict:
        """Search file content with caching"""
        try:
            # Check cache first
            cache_key = str(file_path)
            if cache_key in self._content_cache:
                content = self._content_cache[cache_key]
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Cache if file is small enough
                    if len(content) <= self.config["cache_size_limit"]:
                        self._content_cache[cache_key] = content
                        
            if pattern.search(content):
                stat = file_path.stat()
                return {
                    "path": str(file_path.relative_to(base_path)),
                    "size": self._format_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        self.config["date_format"]
                    ),
                    "type": "file",
                    "matches": len(pattern.findall(content))
                }
        except (OSError, UnicodeDecodeError):
            pass
            
        return None
        
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
