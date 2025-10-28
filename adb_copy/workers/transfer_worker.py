"""File transfer worker module.

Processes file transfer tasks and reports progress in QThread.
"""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

from adb_copy.core.adb_manager import AdbManager


@dataclass
class TransferTask:
    """Data class containing transfer task information.
    
    Attributes:
        task_id: Unique task ID
        filename: Filename
        source_path: Source path
        destination_path: Destination path
        direction: Transfer direction ("push" or "pull")
        device_serial: Device serial number (for remote transfer)
        file_size: File size (bytes)
    """
    task_id: int
    filename: str
    source_path: str
    destination_path: str
    direction: str  # "push" or "pull"
    device_serial: str
    file_size: int


class TransferWorker(QObject):
    """File transfer worker class.
    
    Runs in QThread and sequentially processes file transfer queue.
    
    Signals:
        transfer_started: Emitted when transfer starts (task_id: int)
        transfer_progress: Emitted on progress update (task_id: int, progress: int, speed: str)
        transfer_completed: Emitted when transfer completes (task_id: int)
        transfer_failed: Emitted when transfer fails (task_id: int, error_message: str)
        all_completed: Emitted when all tasks complete
    """
    
    transfer_started = pyqtSignal(int)
    transfer_progress = pyqtSignal(int, int, str)  # task_id, progress%, speed
    transfer_completed = pyqtSignal(int)
    transfer_failed = pyqtSignal(int, str)
    all_completed = pyqtSignal()
    
    def __init__(self, adb_path: str = "adb") -> None:
        """Initialize TransferWorker instance.
        
        Args:
            adb_path: Path to adb executable
        """
        super().__init__()
        self.adb_manager = AdbManager(adb_path)
        self.task_queue: list[TransferTask] = []
        self._running = False
        self._paused = False
    
    def add_task(self, task: TransferTask) -> None:
        """Add transfer task to queue.
        
        Args:
            task: Transfer task
        """
        self.task_queue.append(task)
    
    def start_transfer(self) -> None:
        """Start transfer tasks.
        
        This method must be called from QThread.
        """
        print(f"[DEBUG] TransferWorker.start_transfer started, queue: {len(self.task_queue)} tasks")
        self._running = True
        
        while self._running and self.task_queue:
            # Check for pause
            while self._paused and self._running:
                time.sleep(0.1)
            
            if not self._running:
                break
            
            # Get next task
            task = self.task_queue.pop(0)
            print(f"[DEBUG] Task processing started: task_id={task.task_id}, file={task.filename}")
            
            try:
                self.transfer_started.emit(task.task_id)
                print(f"[DEBUG] transfer_started signal emitted: {task.task_id}")
                
                self._process_task(task)
                print(f"[DEBUG] _process_task completed: {task.task_id}")
                
                self.transfer_completed.emit(task.task_id)
                print(f"[DEBUG] transfer_completed signal emitted: {task.task_id}")
                
            except Exception as e:
                print(f"[DEBUG] Transfer failed: {task.task_id}, error: {str(e)}")
                self.transfer_failed.emit(task.task_id, str(e))
        
        # All tasks completed
        print(f"[DEBUG] Transfer loop ended, remaining tasks: {len(self.task_queue)}")
        if not self.task_queue:
            print("[DEBUG] all_completed signal emitted")
            self.all_completed.emit()
        
        self._running = False
        print("[DEBUG] TransferWorker.start_transfer ended")
    
    def pause(self) -> None:
        """Pause transfer."""
        self._paused = True
    
    def resume(self) -> None:
        """Resume transfer."""
        self._paused = False
    
    def stop(self) -> None:
        """Stop transfer."""
        self._running = False
        self._paused = False
    
    def _process_task(self, task: TransferTask) -> None:
        """Process transfer task.
        
        Args:
            task: Transfer task
            
        Raises:
            Exception: When transfer fails
        """
        if task.direction == "push":
            self._push_file(task)
        elif task.direction == "pull":
            self._pull_file(task)
        else:
            raise ValueError(f"Unknown transfer direction: {task.direction}")
    
    def _push_file(self, task: TransferTask) -> None:
        """Transfer file from local to remote.
        
        Args:
            task: Transfer task
        """
        print(f"[DEBUG] _push_file started: {task.filename}")
        start_time = time.time()
        
        try:
            # ADB push doesn't directly provide progress,
            # so we estimate progress based on file size
            
            # Initial progress
            print(f"[DEBUG] transfer_progress emit: {task.task_id}, 0%")
            self.transfer_progress.emit(task.task_id, 0, "0 KB/s")
            
            # File transfer (blocking)
            print(f"[DEBUG] push_file called: {task.source_path} -> {task.destination_path}")
            self.adb_manager.push_file(
                task.device_serial,
                task.source_path,
                task.destination_path,
                timeout=600,  # 10 minutes
            )
            print(f"[DEBUG] push_file completed")
            
            # Transfer completed
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                speed = task.file_size / elapsed_time / 1024  # KB/s
                speed_str = f"{speed:.1f} KB/s"
            else:
                speed_str = "N/A"
            
            print(f"[DEBUG] transfer_progress emit: {task.task_id}, 100%, {speed_str}")
            self.transfer_progress.emit(task.task_id, 100, speed_str)
            
        except subprocess.SubprocessError as e:
            print(f"[DEBUG] Push failed: {str(e)}")
            raise Exception(f"Push failed: {str(e)}")
    
    def _pull_file(self, task: TransferTask) -> None:
        """Retrieve file from remote to local.
        
        Args:
            task: Transfer task
        """
        print(f"[DEBUG] _pull_file started: {task.filename}")
        start_time = time.time()
        
        try:
            # Initial progress
            print(f"[DEBUG] transfer_progress emit: {task.task_id}, 0%")
            self.transfer_progress.emit(task.task_id, 0, "0 KB/s")
            
            # File transfer (blocking)
            print(f"[DEBUG] pull_file called: {task.source_path} -> {task.destination_path}")
            self.adb_manager.pull_file(
                task.device_serial,
                task.source_path,
                task.destination_path,
                timeout=600,  # 10 minutes
            )
            print(f"[DEBUG] pull_file completed")
            
            # Transfer completed
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                speed = task.file_size / elapsed_time / 1024  # KB/s
                speed_str = f"{speed:.1f} KB/s"
            else:
                speed_str = "N/A"
            
            print(f"[DEBUG] transfer_progress emit: {task.task_id}, 100%, {speed_str}")
            self.transfer_progress.emit(task.task_id, 100, speed_str)
            
        except subprocess.SubprocessError as e:
            print(f"[DEBUG] Pull failed: {str(e)}")
            raise Exception(f"Pull failed: {str(e)}")

