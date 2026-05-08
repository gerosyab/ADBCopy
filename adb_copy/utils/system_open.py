"""Cross-platform helpers for opening files/folders in the OS default
application and for managing ADBCopy's persistent temp directory.
"""

import os
import sys
import subprocess
from pathlib import Path


def open_in_default_app(path) -> None:
    """Open a file or folder using the OS default application.
    
    - Files: launches in the user's default viewer/editor
    - Folders: launches in the OS file explorer (Explorer / Finder / files manager)
    
    Args:
        path: Path to the file or folder (str or Path).
    
    Raises:
        OSError: If the path cannot be opened.
    """
    p = str(path)
    if sys.platform == "win32":
        # os.startfile handles both files (default app) and folders (Explorer)
        os.startfile(p)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", p])
    else:
        # Linux/BSD - desktop environment dependent
        subprocess.Popen(["xdg-open", p])


def get_temp_dir() -> Path:
    """Return ADBCopy's persistent temp directory, creating it if missing.
    
    Located at ~/.adbcopy/temp so it persists across runs (allowing default
    app caching) and is always writable on every platform.
    
    Returns:
        Path to the temp directory.
    """
    p = Path.home() / ".adbcopy" / "temp"
    p.mkdir(parents=True, exist_ok=True)
    return p
