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
        date: Modification date string (e.g., "2025-11-03 15:30")
    """
    name: str
    is_dir: bool
    size: int
    permissions: str
    path: str
    date: str = ""


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
            
            # DEBUG: Print raw output
            print(f"[DEBUG] ls -la output for '{remote_path}':")
            print(f"[DEBUG] Output length: {len(output) if output else 0}")
            print(f"[DEBUG] Output:\n{output}")
            
            # None check
            if output is None:
                self.error_occurred.emit("File list retrieval failed: No output")
                return
            
            files = self._parse_ls_output(output, remote_path)
            print(f"[DEBUG] Parsed {len(files)} files")
            for f in files:
                print(f"[DEBUG]   - {f.name} (is_dir={f.is_dir})")
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
        # lrwxrwxrwx 1 root root      11 2024-10-24 17:33 link -> target
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("total"):
                continue
            
            entry = _parse_ls_line(line)
            if entry is None:
                continue
            
            permissions, size, date_str, name = entry
            
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
                date=date_str,
            ))
        
        # Sort: directories first, then by name
        files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
        
        return files


# Regex shared by single-dir and recursive ls -la parsing.
# Permission (10 chars, includes l for symlinks, s/t for special bits) +
# link count + owner + group + size + date + time + name
_LS_LINE_RE = re.compile(
    r"^([dlrwxst-]{10})\S?\s+\d+\s+\S+\s+\S+\s+(\d+)\s+"
    r"(\d{4}-\d{2}-\d{2}|\w{3}\s+\d{1,2})\s+"
    r"(\d{1,2}:\d{2}|\d{4})\s+"
    r"(.+)$"
)


def _parse_ls_line(line: str):
    """Parse a single ls -la line.
    
    Args:
        line: Single output line from ls -la
        
    Returns:
        Tuple of (permissions, size, date_str, name) or None if not parseable.
        For symlinks, the trailing " -> target" is stripped from name.
    """
    match = _LS_LINE_RE.match(line)
    if not match:
        return None
    
    permissions = match.group(1)
    size = int(match.group(2))
    date_part = match.group(3)
    time_part = match.group(4)
    name = match.group(5)
    
    # Strip "name -> target" for symlinks
    if permissions.startswith("l"):
        arrow_idx = name.find(" -> ")
        if arrow_idx > 0:
            name = name[:arrow_idx]
    
    return permissions, size, f"{date_part} {time_part}", name


def list_files_recursive_sync(
    adb_manager,
    device_serial: str,
    remote_path: str,
    timeout: int = 300,
) -> list[RemoteFileInfo]:
    """Recursively list every regular file under remote_path (synchronous).
    
    Uses `ls -laR` and parses the output. Directories are not returned;
    only files (and symlinks treated as files) are.
    
    Args:
        adb_manager: AdbManager instance
        device_serial: Target device serial
        remote_path: Remote folder to recursively walk
        timeout: Shell command timeout in seconds
        
    Returns:
        Flat list of RemoteFileInfo whose `path` is the absolute remote path.
    """
    output = adb_manager.shell_command(
        device_serial,
        f"ls -laR '{remote_path}'",
        timeout=timeout,
    )
    return _parse_recursive_ls_output(output or "", remote_path)


def _parse_recursive_ls_output(output: str, base_path: str) -> list[RemoteFileInfo]:
    """Parse `ls -laR` output into a flat list of files.
    
    `ls -laR` output looks like:
    
        /sdcard/folder:
        total 16
        drwxrwx--- ... .
        drwxrwx--- ... ..
        -rw-rw---- ... file.txt
        drwxrwx--- ... sub
        
        /sdcard/folder/sub:
        total 8
        ...
    
    Args:
        output: Raw command output
        base_path: The root path passed to ls -laR (used as initial dir)
        
    Returns:
        Flat list of RemoteFileInfo (files only, not directories).
    """
    files: list[RemoteFileInfo] = []
    current_dir = base_path.rstrip("/") or "/"
    
    for raw_line in output.split("\n"):
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("total "):
            continue
        
        # Directory header line: "<path>:" (path is absolute on toybox/Android)
        if line.endswith(":") and line.startswith("/"):
            current_dir = line[:-1] or "/"
            continue
        
        entry = _parse_ls_line(line)
        if entry is None:
            continue
        
        permissions, size, date_str, name = entry
        
        if name in (".", ".."):
            continue
        # Skip directories - we only want flat file list
        if permissions.startswith("d"):
            continue
        
        full_path = f"{current_dir.rstrip('/')}/{name}" if current_dir != "/" else f"/{name}"
        files.append(RemoteFileInfo(
            name=name,
            is_dir=False,
            size=size,
            permissions=permissions,
            path=full_path,
            date=date_str,
        ))
    
    return files

