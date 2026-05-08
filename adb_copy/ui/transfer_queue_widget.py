"""Transfer queue widget module.

Displays and manages ongoing file transfer tasks.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from adb_copy.i18n import tr, get_translator


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
    tasks_removed = pyqtSignal(list)  # list[int] of removed task_ids
    
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
        
        # Live language switching
        get_translator().add_language_listener(self._retranslate_ui)
    
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
        
        # Remove drop-down (replaces "Clear Completed")
        self.remove_button = QToolButton()
        self.remove_button.setText(tr("Remove") + " ▼")
        self.remove_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.remove_menu = QMenu(self.remove_button)
        
        self.action_remove_selected = QAction(tr("Remove Selected"), self)
        self.action_remove_selected.triggered.connect(self._remove_selected)
        self.remove_menu.addAction(self.action_remove_selected)
        
        self.remove_menu.addSeparator()
        
        self.action_remove_completed = QAction(tr("Remove Completed"), self)
        self.action_remove_completed.triggered.connect(self._remove_completed)
        self.remove_menu.addAction(self.action_remove_completed)
        
        self.action_remove_failed = QAction(tr("Remove Failed"), self)
        self.action_remove_failed.triggered.connect(self._remove_failed)
        self.remove_menu.addAction(self.action_remove_failed)
        
        self.action_remove_waiting = QAction(tr("Remove Waiting"), self)
        self.action_remove_waiting.triggered.connect(self._remove_waiting)
        self.remove_menu.addAction(self.action_remove_waiting)
        
        self.action_remove_finished = QAction(tr("Remove Finished"), self)
        self.action_remove_finished.triggered.connect(self._remove_finished)
        self.remove_menu.addAction(self.action_remove_finished)
        
        self.remove_menu.addSeparator()
        
        self.action_remove_all = QAction(tr("Remove All"), self)
        self.action_remove_all.triggered.connect(self._remove_all)
        self.remove_menu.addAction(self.action_remove_all)
        
        self.remove_button.setMenu(self.remove_menu)
        info_layout.addWidget(self.remove_button)
        
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
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        # No max height limit (controlled by Splitter)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
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
    
    def _remove_rows_by_filter(self, predicate) -> list:
        """Remove rows where predicate(row, status_text, task_id) returns True.
        
        Always skips in-progress rows so the worker isn't disturbed.
        Returns the list of removed task_ids.
        """
        in_progress_text = tr("⚡ Transferring")
        rows_to_remove: list[int] = []
        removed_ids: list[int] = []
        
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 0)
            if not status_item:
                continue
            text = status_item.text()
            if text == in_progress_text:
                continue  # never disturb a running transfer
            task_id = status_item.data(Qt.ItemDataRole.UserRole)
            if predicate(row, text, task_id):
                rows_to_remove.append(row)
                if task_id is not None:
                    removed_ids.append(task_id)
                # Also clean any tracked start time
                self._task_start_times.pop(task_id, None)
        
        for row in reversed(rows_to_remove):
            self.table.removeRow(row)
        
        self._update_status_stats()
        if removed_ids:
            self.tasks_removed.emit(removed_ids)
        return removed_ids
    
    def _has_in_progress(self) -> bool:
        """Return True if any row is currently transferring."""
        in_progress_text = tr("⚡ Transferring")
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 0)
            if status_item and status_item.text() == in_progress_text:
                return True
        return False
    
    def _count_in_progress(self) -> int:
        in_progress_text = tr("⚡ Transferring")
        n = 0
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 0)
            if status_item and status_item.text() == in_progress_text:
                n += 1
        return n
    
    def _selected_rows(self) -> set:
        return set(item.row() for item in self.table.selectedItems())
    
    def _remove_selected(self) -> None:
        rows = self._selected_rows()
        if not rows:
            return
        self._remove_rows_by_filter(lambda r, text, tid: r in rows)
    
    def _remove_completed(self) -> None:
        completed = tr("✓ Completed")
        self._remove_rows_by_filter(lambda r, text, tid: text == completed)
    
    def _remove_failed(self) -> None:
        failed = tr("✗ Failed")
        self._remove_rows_by_filter(lambda r, text, tid: text == failed)
    
    def _remove_waiting(self) -> None:
        waiting = tr("⏳ Waiting")
        self._remove_rows_by_filter(lambda r, text, tid: text == waiting)
    
    def _remove_finished(self) -> None:
        finished = {tr("✓ Completed"), tr("✗ Failed")}
        self._remove_rows_by_filter(lambda r, text, tid: text in finished)
    
    def _remove_all(self) -> None:
        in_progress = self._count_in_progress()
        if in_progress > 0:
            msg = tr("Remove all queued items?") + "\n\n" + tr("In-progress items will be kept ({0}).").format(in_progress)
        else:
            msg = tr("Remove all queued items?")
        reply = QMessageBox.question(
            self,
            tr("Confirm Remove All"),
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._remove_rows_by_filter(lambda r, text, tid: True)
    
    # Backward-compat alias (kept in case external code calls it)
    def _on_clear_completed(self) -> None:
        self._remove_completed()
    
    def _show_context_menu(self, position) -> None:
        """Right-click menu on the queue table."""
        menu = QMenu(self)
        has_selection = bool(self._selected_rows())
        
        sel_action = QAction(tr("Remove Selected"), self)
        sel_action.setEnabled(has_selection)
        sel_action.triggered.connect(self._remove_selected)
        menu.addAction(sel_action)
        
        menu.addSeparator()
        
        comp_action = QAction(tr("Remove Completed"), self)
        comp_action.triggered.connect(self._remove_completed)
        menu.addAction(comp_action)
        
        fail_action = QAction(tr("Remove Failed"), self)
        fail_action.triggered.connect(self._remove_failed)
        menu.addAction(fail_action)
        
        wait_action = QAction(tr("Remove Waiting"), self)
        wait_action.triggered.connect(self._remove_waiting)
        menu.addAction(wait_action)
        
        fin_action = QAction(tr("Remove Finished"), self)
        fin_action.triggered.connect(self._remove_finished)
        menu.addAction(fin_action)
        
        menu.addSeparator()
        
        all_action = QAction(tr("Remove All"), self)
        all_action.triggered.connect(self._remove_all)
        menu.addAction(all_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
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
    
    def _retranslate_ui(self, _lang: str = "") -> None:
        """Refresh translatable UI text after a language change."""
        # Column headers
        self.table.setHorizontalHeaderLabels([
            tr("Status"), tr("Filename"), tr("Source"), tr("Destination"), tr("Time(sec)"),
        ])
        # Buttons
        self.pause_button.setText(tr("Resume") if self._paused else tr("Pause"))
        self.retry_button.setText(tr("Retry Failed"))
        # Remove drop-down
        self.remove_button.setText(tr("Remove") + " ▼")
        self.action_remove_selected.setText(tr("Remove Selected"))
        self.action_remove_completed.setText(tr("Remove Completed"))
        self.action_remove_failed.setText(tr("Remove Failed"))
        self.action_remove_waiting.setText(tr("Remove Waiting"))
        self.action_remove_finished.setText(tr("Remove Finished"))
        self.action_remove_all.setText(tr("Remove All"))
        # Progress bar format
        self.global_progress_bar.setFormat(tr("Overall Progress") + ": %p%")
        
        # Re-translate per-row Status column. Status cells store the
        # human-readable label, so we rewrite them based on a tag column
        # Inferred from the previous text in any language.
        status_map_en = {
            "⏳ Waiting": tr("⏳ Waiting"),
            "⚡ Transferring": tr("⚡ Transferring"),
            "✓ Completed": tr("✓ Completed"),
            "✗ Failed": tr("✗ Failed"),
        }
        # Build reverse dict: any prior text -> emoji-prefixed key -> new translated
        # Emojis are language-independent so we can detect by the leading emoji.
        prefix_to_key = {
            "⏳": "⏳ Waiting",
            "⚡": "⚡ Transferring",
            "✓": "✓ Completed",
            "✗": "✗ Failed",
        }
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 0)
            if not status_item:
                continue
            cur = status_item.text()
            if not cur:
                continue
            for prefix, key in prefix_to_key.items():
                if cur.startswith(prefix):
                    status_item.setText(status_map_en[key])
                    break
        
        # Refresh stats (status_label, global_progress_label)
        self._update_status_stats()
    
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

