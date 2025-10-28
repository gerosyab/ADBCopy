"""ADB command management module.

This module wraps all ADB commands with subprocess.
Contains only pure Python logic and never imports PyQt6.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Windows subprocess optimization for PyInstaller
if sys.platform == 'win32':
    # Create startup info to hide console window and optimize process creation
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _STARTUPINFO.wShowWindow = subprocess.SW_HIDE
    
    # Creation flags for faster process creation
    _CREATION_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    _STARTUPINFO = None
    _CREATION_FLAGS = 0


@dataclass
class AdbDevice:
    """Data class containing ADB device information.
    
    Attributes:
        serial: Device serial number (e.g., "RF8M12345AB")
        state: Device state (e.g., "device", "offline", "unauthorized")
        model: Device model name (optional)
    """
    serial: str
    state: str
    model: str | None = None


class AdbManager:
    """Class that manages ADB commands.
    
    All ADB commands are executed through this class.
    Uses subprocess and provides timeout and error handling.
    """
    
    def __init__(self, adb_path: str = "adb") -> None:
        """Initialize AdbManager instance.
        
        Args:
            adb_path: Path to adb executable. Default is "adb" (searches in PATH)
        """
        self.adb_path = adb_path
    
    def get_devices(self) -> list[AdbDevice]:
        """Get list of connected ADB devices.
        
        Returns:
            List of AdbDevice. Empty list if no devices connected.
            
        Raises:
            subprocess.SubprocessError: When adb command execution fails
        """
        try:
            result = subprocess.run(
                [self.adb_path, "devices", "-l"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5,
                check=True,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
            
            devices = []
            # Skip first line "List of devices attached"
            for line in result.stdout.strip().split("\n")[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # Format: "serial state model:xxx device:xxx"
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    state = parts[1]
                    
                    # Extract model info (if available)
                    model = None
                    for part in parts[2:]:
                        if part.startswith("model:"):
                            model = part.split(":", 1)[1]
                            break
                    
                    devices.append(AdbDevice(serial=serial, state=state, model=model))
            
            return devices
            
        except subprocess.TimeoutExpired:
            raise subprocess.SubprocessError("ADB devices command timeout")
        except subprocess.CalledProcessError as e:
            raise subprocess.SubprocessError(f"ADB devices execution failed: {e.stderr}")
        except FileNotFoundError:
            raise subprocess.SubprocessError(
                f"ADB executable not found: {self.adb_path}"
            )
    
    def check_adb_available(self) -> bool:
        """Check if ADB is available.
        
        Returns:
            bool: Whether ADB is executable
        """
        try:
            subprocess.run(
                [self.adb_path, "version"],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=3,
                check=True,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def shell_command(
        self,
        device_serial: str,
        command: str,
        timeout: int = 30,
    ) -> str:
        """Execute shell command on specific device.
        
        Args:
            device_serial: Target device serial number
            command: Shell command to execute
            timeout: Timeout (seconds). Default 30 seconds
            
        Returns:
            str: Command execution result (stdout)
            
        Raises:
            subprocess.SubprocessError: When command execution fails
        """
        try:
            result = subprocess.run(
                [self.adb_path, "-s", device_serial, "shell", command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace with ? on decode failure
                timeout=timeout,
                check=True,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise subprocess.SubprocessError(f"Shell command timeout: {command}")
        except subprocess.CalledProcessError as e:
            raise subprocess.SubprocessError(
                f"Shell command execution failed: {e.stderr}"
            )
    
    def pull_file(
        self,
        device_serial: str,
        remote_path: str,
        local_path: str,
        timeout: int = 300,
    ) -> None:
        """Pull file from device to local.
        
        Args:
            device_serial: Target device serial number
            remote_path: File path on device
            local_path: Local save path
            timeout: Timeout (seconds). Default 300 seconds (5 minutes)
            
        Raises:
            subprocess.SubprocessError: When file transfer fails
        """
        try:
            subprocess.run(
                [self.adb_path, "-s", device_serial, "pull", remote_path, local_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                check=True,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
        except subprocess.TimeoutExpired:
            raise subprocess.SubprocessError(f"Pull timeout: {remote_path}")
        except subprocess.CalledProcessError as e:
            raise subprocess.SubprocessError(f"Pull failed: {e.stderr}")
    
    def push_file(
        self,
        device_serial: str,
        local_path: str,
        remote_path: str,
        timeout: int = 300,
    ) -> None:
        """Push file from local to device.
        
        Args:
            device_serial: Target device serial number
            local_path: Local file path
            remote_path: Save path on device
            timeout: Timeout (seconds). Default 300 seconds (5 minutes)
            
        Raises:
            subprocess.SubprocessError: When file transfer fails
        """
        try:
            subprocess.run(
                [self.adb_path, "-s", device_serial, "push", local_path, remote_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                check=True,
                startupinfo=_STARTUPINFO,
                creationflags=_CREATION_FLAGS,
            )
        except subprocess.TimeoutExpired:
            raise subprocess.SubprocessError(f"Push timeout: {local_path}")
        except subprocess.CalledProcessError as e:
            raise subprocess.SubprocessError(f"Push failed: {e.stderr}")
    
    def delete_file(
        self,
        device_serial: str,
        remote_path: str,
        is_dir: bool = False,
    ) -> None:
        """Delete remote file/folder.
        
        Args:
            device_serial: Target device serial number
            remote_path: Remote path to delete
            is_dir: Whether it's a directory
            
        Raises:
            subprocess.SubprocessError: When deletion fails
        """
        try:
            command = f"rm -rf '{remote_path}'" if is_dir else f"rm '{remote_path}'"
            self.shell_command(device_serial, command, timeout=10)
        except subprocess.SubprocessError as e:
            raise subprocess.SubprocessError(f"Deletion failed: {str(e)}")
    
    def create_directory(
        self,
        device_serial: str,
        remote_path: str,
    ) -> None:
        """Create remote directory.
        
        Args:
            device_serial: Target device serial number
            remote_path: Directory path to create
            
        Raises:
            subprocess.SubprocessError: When creation fails
        """
        try:
            command = f"mkdir -p '{remote_path}'"
            self.shell_command(device_serial, command, timeout=10)
        except subprocess.SubprocessError as e:
            raise subprocess.SubprocessError(f"Directory creation failed: {str(e)}")
    
    def rename_file(
        self,
        device_serial: str,
        old_path: str,
        new_path: str,
    ) -> None:
        """Rename remote file/folder.
        
        Args:
            device_serial: Target device serial number
            old_path: Old path
            new_path: New path
            
        Raises:
            subprocess.SubprocessError: When renaming fails
        """
        try:
            command = f"mv '{old_path}' '{new_path}'"
            self.shell_command(device_serial, command, timeout=10)
        except subprocess.SubprocessError as e:
            raise subprocess.SubprocessError(f"Rename failed: {str(e)}")
    
    def file_exists(
        self,
        device_serial: str,
        remote_path: str,
    ) -> bool:
        """Check if remote file/folder exists.
        
        Args:
            device_serial: Target device serial number
            remote_path: Path to check
            
        Returns:
            Whether it exists
        """
        try:
            # Check existence with test command (most accurate)
            command = f"test -e '{remote_path}' && echo 'YES' || echo 'NO'"
            result = self.shell_command(device_serial, command, timeout=5)
            result_clean = result.strip()
            print(f"[DEBUG] file_exists({remote_path}): result='{result_clean}'")
            exists = result_clean == "YES"
            print(f"[DEBUG] file_exists return value: {exists}")
            return exists
        except subprocess.SubprocessError as e:
            print(f"[DEBUG] file_exists error: {str(e)}")
            return False

