"""Transfer queue widget module.

Displays and manages ongoing file transfer tasks.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from adb_copy.i18n import tr


class TransferQueueWidget(QWidget):
    """Transfer queue widget class.
    
    Displays waiting/in-progress/completed/failed file list.
    
    Signals:
        files_dropped: Emitted when files are dropped (list[dict]: file info)
        pause_clicked: Emitted when pause button is clicked
        retry_clicked: Emitted when retry button is clicked
    """
    
    files_dropped = pyqtSignal(list)
    pause_clicked = pyqtSignal()
    retry_clicked = pyqtSignal()
    
    def __init__(self) -> None:
        """Initialize TransferQueueWidget instance."""
        super().__init__()
        self._paused = False
        self._task_start_times = {}  # task_id: start_time (seconds)
        self._init_ui()
        
        # Timer for real-time stats update (every 1 second)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status_stats)
        self._update_timer.start(1000)  # Update every 1 second
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Progress bar top spacing
        layout.addSpacing(5)
        
        # Overall progress bar
        self.global_progress_bar = QProgressBar()
        self.global_progress_bar.setMinimumHeight(20)
        self.global_progress_bar.setValue(0)
        self.global_progress_bar.setFormat(tr("Overall Progress") + ": %p%")
        self.global_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #999999;
                border-radius: 3px;
                text-align: center;
                font-size: 9pt;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4A9EFF;
            }
        """)
        layout.addWidget(self.global_progress_bar)
        
        # Progress bar bottom spacing
        layout.addSpacing(3)
        
        # Top information area
        info_layout = QHBoxLayout()
        
        # Left: Overall progress info
        self.global_progress_label = QLabel(tr("Time") + ": -")
        self.global_progress_label.setStyleSheet("font-weight: bold; color: #2E7ED4;")
        info_layout.addWidget(self.global_progress_label)
        
        info_layout.addSpacing(20)
        
        # Right: Task statistics
        self.status_label = QLabel(f"{tr('Waiting')}: 0 | {tr('In Progress')}: 0 | {tr('Completed')}: 0 | {tr('Failed')}: 0")
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        
        # Buttons
        self.pause_button = QPushButton(tr("Pause"))
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        info_layout.addWidget(self.pause_button)
        
        self.retry_button = QPushButton(tr("Retry Failed"))
        self.retry_button.setEnabled(False)
        self.retry_button.clicked.connect(self._on_retry_clicked)
        info_layout.addWidget(self.retry_button)
        
        self.clear_button = QPushButton(tr("Clear Completed"))
        self.clear_button.clicked.connect(self._on_clear_completed)
        info_layout.addWidget(self.clear_button)
        
        layout.addLayout(info_layout)
        
        # Transfer list table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            tr("Status"), tr("Filename"), tr("Source"), tr("Destination"), tr("Time(sec)")
        ])
        
        # Column size adjustment (filename/source/destination similar sizes)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Filename
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Source
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Destination
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Time
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        # No max height limit (controlled by Splitter)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Improve hover/selection colors
        self.table.setStyleSheet("""
            QTableWidget {
                selection-background-color: #A8D3FF;  /* Light blue */
                selection-color: #000000;  /* Black text */
            }
            QTableWidget::item:hover {
                background-color: #E8E8E8;  /* Light gray */
            }
            QTableWidget::item:selected {
                background-color: #A8D3FF;  /* Light blue */
                color: #000000;  /* Black text */
            }
        """)
        
        layout.addWidget(self.table)
    
    def add_transfer(
        self,
        task_id: int,
        filename: str,
        source: str,
        destination: str,
        skip_stats_update: bool = False,
        file_size: int = 0,
    ) -> int:
        """Add transfer task.
        
        Args:
            task_id: Task ID
            filename: Filename
            source: Source path
            destination: Destination path
            skip_stats_update: Skip stats update (for batch processing)
            file_size: File size (bytes)
            
        Returns:
            Added row index
        """
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Temporarily disable sorting (prevent sorting during add)
        sorting_enabled = self.table.isSortingEnabled()
        if sorting_enabled:
            self.table.setSortingEnabled(False)
        
        # Status (store task_id and file_size in UserRole)
        status_item = QTableWidgetItem(tr("⏳ Waiting"))
        status_item.setData(Qt.ItemDataRole.UserRole, task_id)
        status_item.setData(Qt.ItemDataRole.UserRole + 1, file_size)  # Store file size
        self.table.setItem(row, 0, status_item)
        
        # Filename
        name_item = QTableWidgetItem(filename)
        self.table.setItem(row, 1, name_item)
        
        # Source
        source_item = QTableWidgetItem(source)
        self.table.setItem(row, 2, source_item)
        
        # Destination
        dest_item = QTableWidgetItem(destination)
        self.table.setItem(row, 3, dest_item)
        
        # Time (seconds)
        time_item = QTableWidgetItem("-")
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 4, time_item)
        
        # Re-enable sorting
        if sorting_enabled:
            self.table.setSortingEnabled(True)
        
        # Update stats (skip during batch processing)
        if not skip_stats_update:
            self._update_status_stats()
        
        return row
    
    def update_progress_by_task_id(
        self,
        task_id: int,
        progress: int,
        speed: str = "",
        time_info: str = "",
    ) -> None:
        """Update transfer progress by task_id.
        
        Args:
            task_id: Task ID
            progress: Progress (0-100)
            speed: Transfer speed string (unused)
            time_info: Time info string (unused)
        """
        import time
        
        # Find row by task_id
        row = self._find_row_by_task_id(task_id)
        if row == -1:
            print(f"[DEBUG] Cannot find row for task_id {task_id}")
            return
        
        print(f"[DEBUG] update_progress_by_task_id: task_id={task_id}, row={row}, progress={progress}")
        
        # Update status
        status_item = self.table.item(row, 0)
        if status_item:
            if progress == 0:
                # Record transfer start time
                self._task_start_times[task_id] = time.time()
                status_item.setText(tr("⚡ Transferring"))
            elif progress == 100:
                # Calculate transfer completion time
                if task_id in self._task_start_times:
                    elapsed = time.time() - self._task_start_times[task_id]
                    time_item = self.table.item(row, 4)
                    if time_item:
                        time_item.setText(f"{elapsed:.1f}")
                    del self._task_start_times[task_id]
                status_item.setText(tr("✓ Completed"))
            else:
                status_item.setText(tr("⚡ Transferring"))
        
        # Auto-scroll to current transferring item
        if progress < 100:
            self.table.scrollToItem(status_item, QTableWidget.ScrollHint.PositionAtCenter)
        
        # Update stats
        self._update_status_stats()
    
    def mark_failed_by_task_id(self, task_id: int, error_message: str) -> None:
        """Mark transfer as failed by task_id.
        
        Args:
            task_id: Task ID
            error_message: Error message
        """
        row = self._find_row_by_task_id(task_id)
        if row == -1:
            return
        
        status_item = self.table.item(row, 0)
        if status_item:
            status_item.setText(tr("✗ Failed"))
        
        # Remove time display (on failure)
        if task_id in self._task_start_times:
            del self._task_start_times[task_id]
        
        time_item = self.table.item(row, 4)
        if time_item:
            time_item.setText(tr("Failed"))
        
        # Update stats
        self._update_status_stats()
    
    def _find_row_by_task_id(self, task_id: int) -> int:
        """Find row index by task_id.
        
        Args:
            task_id: Task ID
            
        Returns:
            Row index. Returns -1 if not found
        """
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 0)
            if status_item and status_item.data(Qt.ItemDataRole.UserRole) == task_id:
                return row
        return -1
    
    def update_progress(
        self,
        row: int,
        progress: int,
        speed: str = "",
        time_info: str = "",
    ) -> None:
        """Update transfer progress. (Legacy, task_id version recommended)
        
        Args:
            row: Row index
            progress: Progress (0-100)
            speed: Transfer speed string
            time_info: Time info string
        """
        if row < 0 or row >= self.table.rowCount():
            return
        
        # Update status
        status_item = self.table.item(row, 0)
        if status_item:
            if progress == 100:
                status_item.setText(tr("✓ Completed"))
            else:
                status_item.setText(tr("⚡ Transferring"))
        
        # Update progress (legacy code, column 4 no longer has progress bar)
        # Kept for compatibility but does nothing
    
    def mark_failed(self, row: int, error_message: str) -> None:
        """Mark transfer as failed. (Legacy)
        
        Args:
            row: Row index
            error_message: Error message
        """
        if row < 0 or row >= self.table.rowCount():
            return
        
        status_item = self.table.item(row, 0)
        if status_item:
            status_item.setText(tr("✗ Failed"))
    
    def _on_clear_completed(self) -> None:
        """Remove completed transfer items."""
        rows_to_remove = []
        
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 0)
            if status_item and status_item.text() == tr("✓ Completed"):
                rows_to_remove.append(row)
        
        # Remove in reverse order (prevent index changes)
        for row in reversed(rows_to_remove):
            self.table.removeRow(row)
        
        # Update stats
        self._update_status_stats()
    
    def _on_pause_clicked(self) -> None:
        """Pause/resume button click handler."""
        self._paused = not self._paused
        
        if self._paused:
            self.pause_button.setText(tr("Resume"))
        else:
            self.pause_button.setText(tr("Pause"))
        
        self.pause_clicked.emit()
    
    def _on_retry_clicked(self) -> None:
        """Retry button click handler."""
        self.retry_clicked.emit()
    
    def enable_pause_button(self, enabled: bool) -> None:
        """Enable/disable pause button.
        
        Args:
            enabled: Enable status
        """
        self.pause_button.setEnabled(enabled)
    
    def enable_retry_button(self, enabled: bool) -> None:
        """Enable/disable retry button.
        
        Args:
            enabled: Enable status
        """
        self.retry_button.setEnabled(enabled)
    
    def _update_status_stats(self) -> None:
        """Update top status statistics."""
        import time
        
        total = self.table.rowCount()
        waiting = 0
        in_progress = 0
        completed = 0
        failed = 0
        
        total_elapsed = 0.0
        in_progress_tasks = []
        
        for row in range(total):
            status_item = self.table.item(row, 0)
            if not status_item:
                continue
            
            status_text = status_item.text()
            task_id = status_item.data(Qt.ItemDataRole.UserRole)
            
            if status_text == tr("⏳ Waiting"):
                waiting += 1
            elif status_text == tr("⚡ Transferring"):
                in_progress += 1
                if task_id in self._task_start_times:
                    in_progress_tasks.append(task_id)
            elif status_text == tr("✓ Completed"):
                completed += 1
                # Sum completed task times
                time_item = self.table.item(row, 4)
                if time_item and time_item.text() not in ["-", tr("Failed")]:
                    try:
                        total_elapsed += float(time_item.text())
                    except ValueError:
                        pass
            elif status_text == tr("✗ Failed"):
                failed += 1
        
        # Add elapsed time for in-progress tasks
        current_time = time.time()
        for task_id in in_progress_tasks:
            if task_id in self._task_start_times:
                total_elapsed += (current_time - self._task_start_times[task_id])
        
        # Calculate overall progress
        if total > 0:
            progress_percent = (completed / total) * 100
        else:
            progress_percent = 0
        
        # Update progress bar
        self.global_progress_bar.setValue(int(progress_percent))
        
        # Calculate average speed and time
        speed_text = "-"
        estimated_time_text = "-"
        
        # Calculate total size of completed files
        total_bytes = 0
        for row in range(total):
            status_item = self.table.item(row, 0)
            if status_item and status_item.text() == tr("✓ Completed"):
                file_size = status_item.data(Qt.ItemDataRole.UserRole + 1)
                if file_size:
                    total_bytes += file_size
        
        if completed > 0 and total_elapsed > 0:
            # Average transfer speed (MB/s)
            if total_bytes > 0:
                mb_transferred = total_bytes / (1024 * 1024)
                mb_per_second = mb_transferred / total_elapsed
                speed_text = f"{mb_per_second:.1f} MB/s"
            else:
                speed_text = "- MB/s"
            
            # Average transfer time = total elapsed time / completed count
            avg_time_per_file = total_elapsed / completed
            
            # Remaining tasks
            remaining = waiting + in_progress
            
            if remaining > 0:
                # Estimated remaining time
                estimated_remaining = avg_time_per_file * remaining
                
                # Display elapsed/estimated time (HH:MM:SS)
                def format_time_hms(seconds):
                    hours = int(seconds // 3600)
                    minutes = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
                
                elapsed_text = format_time_hms(total_elapsed)
                remaining_text = format_time_hms(estimated_remaining)
                
                estimated_time_text = f"{elapsed_text}/{remaining_text}"
            else:
                # All completed
                def format_time_hms(seconds):
                    hours = int(seconds // 3600)
                    minutes = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
                
                estimated_time_text = format_time_hms(total_elapsed)
        
        # Update status
        self.status_label.setText(f"{tr('Waiting')}: {waiting} | {tr('In Progress')}: {in_progress} | {tr('Completed')}: {completed} | {tr('Failed')}: {failed}")
        
        # Update overall progress info
        if total > 0:
            self.global_progress_label.setText(f"{tr('Time')}: {estimated_time_text} | {tr('Speed')}: {speed_text}")
        else:
            self.global_progress_label.setText(f"{tr('Time')}: - | {tr('Speed')}: -")
        
        # Enable/disable retry failed button
        self.enable_retry_button(failed > 0)

