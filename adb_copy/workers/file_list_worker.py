"""File list retrieval worker module.

Executes `adb shell ls` command in QThread to
asynchronously retrieve file list from remote device.
"""

import re
import subprocess
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from adb_copy.core.adb_manager import AdbManager


@dataclass
class RemoteFileInfo:
    """Data class containing remote file information.
    
    Attributes:
        name: File/directory name
        is_dir: Whether it's a directory
        size: File size (bytes). 0 for directories
        permissions: Permission string (e.g., "drwxr-xr-x")
        path: Full path
    """
    name: str
    is_dir: bool
    size: int
    permissions: str
    path: str


class FileListWorker(QObject):
    """File list retrieval worker class.
    
    Runs in QThread and asynchronously retrieves directory contents from remote device.
    
    Signals:
        files_loaded: Emitted when file list retrieval completes (list[RemoteFileInfo])
        error_occurred: Emitted when error occurs (str)
    """
    
    files_loaded = pyqtSignal(list)  # list[RemoteFileInfo]
    error_occurred = pyqtSignal(str)
    
    def __init__(self, adb_path: str = "adb") -> None:
        """Initialize FileListWorker instance.
        
        Args:
            adb_path: Path to adb executable
        """
        super().__init__()
        self.adb_manager = AdbManager(adb_path)
    
    def list_files(self, device_serial: str, remote_path: str) -> None:
        """Retrieve file list from remote directory.
        
        This method must be called from QThread.
        
        Args:
            device_serial: Target device serial number
            remote_path: Remote directory path to query
        """
        try:
            # Execute ls -la command (with detailed info)
            output = self.adb_manager.shell_command(
                device_serial,
                f"ls -la '{remote_path}'",
                timeout=10,
            )
            
            # None check
            if output is None:
                self.error_occurred.emit("File list retrieval failed: No output")
                return
            
            files = self._parse_ls_output(output, remote_path)
            self.files_loaded.emit(files)
            
        except subprocess.SubprocessError as e:
            self.error_occurred.emit(f"File list retrieval failed: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
    
    def _parse_ls_output(
        self,
        output: str,
        base_path: str,
    ) -> list[RemoteFileInfo]:
        """Parse ls -la output.
        
        Args:
            output: Output from ls -la command
            base_path: Base path
            
        Returns:
            List of RemoteFileInfo
        """
        files = []
        
        # Check for empty output
        if not output or not output.strip():
            return files
        
        lines = output.strip().split("\n")
        
        # ls -la output format:
        # drwxr-xr-x  2 root root  4096 2024-10-24 17:33 dirname
        # -rw-r--r--  1 root root  1234 2024-10-24 17:33 filename with spaces.txt
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("total"):
                continue
            
            # Parse with regex
            # Permission (10 chars) + link count + owner + group + size + date + time + name
            # Explicitly match date/time formats (YYYY-MM-DD HH:MM or Mon DD HH:MM or Mon DD YYYY)
            match = re.match(
                r"^([drwx-]{10})\s+\d+\s+\S+\s+\S+\s+(\d+)\s+"  # Permission~size
                r"(?:\d{4}-\d{2}-\d{2}|\w{3}\s+\d{1,2})\s+"  # Date part
                r"(?:\d{1,2}:\d{2}|\d{4})\s+"  # Time or year
                r"(.+)$",  # Filename (rest of line)
                line,
            )
            
            if not match:
                continue
            
            permissions = match.group(1)
            size = int(match.group(2))
            name = match.group(3)
            
            # Exclude . and ..
            if name in (".", ".."):
                continue
            
            is_dir = permissions.startswith("d")
            full_path = f"{base_path.rstrip('/')}/{name}"
            
            files.append(RemoteFileInfo(
                name=name,
                is_dir=is_dir,
                size=size,
                permissions=permissions,
                path=full_path,
            ))
        
        # Sort: directories first, then by name
        files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
        
        return files

