"""
Search implementation and utilities.
"""
import subprocess
from pathlib import Path
from typing import List, Generator

def execute_search(cmd: List[str]) -> Generator[str, None, None]:
    """Execute search command and yield results"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            yield line.strip()

    if process.returncode != 0:
        raise RuntimeError(process.stderr.read())
