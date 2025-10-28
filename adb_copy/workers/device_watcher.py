"""Device watcher worker module.

Periodically executes `adb devices` in QThread to detect
device connection state changes and notify via signals.
"""

import subprocess
import time
from PyQt6.QtCore import QObject, pyqtSignal

from adb_copy.core.adb_manager import AdbDevice, AdbManager


class DeviceWatcher(QObject):
    """Worker class that monitors device connection state.
    
    Runs in QThread and periodically checks connected device list.
    Emits signals when device list changes.
    
    Signals:
        devices_changed: Emitted when device list changes (list[AdbDevice])
        error_occurred: Emitted when error occurs (str)
    """
    
    devices_changed = pyqtSignal(list)  # list[AdbDevice]
    error_occurred = pyqtSignal(str)
    
    def __init__(self, adb_path: str = "adb", poll_interval: float = 2.0) -> None:
        """Initialize DeviceWatcher instance.
        
        Args:
            adb_path: Path to adb executable
            poll_interval: Polling interval (seconds). Default 2 seconds
        """
        super().__init__()
        self.adb_manager = AdbManager(adb_path)
        self.poll_interval = poll_interval
        self._running = False
        self._last_devices: list[AdbDevice] = []
    
    def start_watching(self) -> None:
        """Start device monitoring.
        
        This method must be called from QThread and
        will block until stop_watching() is called.
        """
        self._running = True
        
        while self._running:
            try:
                current_devices = self.adb_manager.get_devices()
                
                # Check if device list changed
                if self._devices_changed(current_devices):
                    self._last_devices = current_devices
                    self.devices_changed.emit(current_devices)
                
            except subprocess.SubprocessError as e:
                self.error_occurred.emit(str(e))
            
            # Wait for polling interval
            time.sleep(self.poll_interval)
    
    def stop_watching(self) -> None:
        """Stop device monitoring."""
        self._running = False
    
    def _devices_changed(self, current_devices: list[AdbDevice]) -> bool:
        """Compare previous device list with current list.
        
        Args:
            current_devices: Current device list
            
        Returns:
            bool: Whether device list has changed
        """
        if len(current_devices) != len(self._last_devices):
            return True
        
        # Compare by serial number and state
        current_set = {(d.serial, d.state) for d in current_devices}
        last_set = {(d.serial, d.state) for d in self._last_devices}
        
        return current_set != last_set

