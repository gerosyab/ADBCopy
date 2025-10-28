"""ADBCopy main window.

Implements FileZilla-style vertical layout.
Top: Console, Middle: Dual panels, Bottom: Transfer queue
"""

from pathlib import Path
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QAction, QIcon

from adb_copy.core.adb_manager import AdbDevice, AdbManager
from adb_copy.workers.device_watcher import DeviceWatcher
from adb_copy.workers.transfer_worker import TransferWorker, TransferTask
from adb_copy.ui.console_widget import ConsoleWidget
from adb_copy.ui.file_panel import FilePanel
from adb_copy.ui.transfer_queue_widget import TransferQueueWidget
from adb_copy.ui.overwrite_dialog import OverwriteDialog
from adb_copy.i18n import tr, set_language, get_language
from adb_copy.config import get_config, set_config


class MainWindow(QMainWindow):
    """ADBCopy main window class.
    
    Implements FileZilla-style vertical layout.
    """
    
    def __init__(self) -> None:
        """Initialize MainWindow instance."""
        super().__init__()
        
        # Load saved language
        saved_language = get_config("language", "ko")
        set_language(saved_language)
        
        self.setWindowTitle(tr("ADBCopy - ADB File Explorer"))
        self.setMinimumSize(1200, 800)
        
        # Set window icon
        icon_path = Path(__file__).parent / "resources" / "icons" / "ADBCopy.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Transfer-related variables
        self._drag_source_files: list[dict] = []
        self._next_task_id = 1
        self._overwrite_all_action: int | None = None  # Store "apply to all" action
        self.adb_manager = AdbManager()
        
        self._init_ui()
        self._init_menubar()
        self._init_statusbar()
        self._init_device_watcher()
        self._init_transfer_worker()
    
    def _init_ui(self) -> None:
        """Initialize main UI layout.
        
        Arranges 3 vertical areas:
        1. Console (top)
        2. Dual file panels (middle)
        3. Transfer queue (bottom)
        """
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # QSplitter for resizable areas
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Splitter handle style (thin drag area)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #CCCCCC;
                height: 2px;
            }
            QSplitter::handle:hover {
                background-color: #4A9EFF;
                height: 3px;
            }
            QSplitter::handle:pressed {
                background-color: #2E7ED4;
                height: 3px;
            }
        """)
        
        # 1. Console widget (top)
        self.console = ConsoleWidget()
        self.console.setMinimumHeight(100)  # Minimum height 100px
        main_splitter.addWidget(self.console)
        
        # 2. Dual panel area (middle)
        panels_layout = QHBoxLayout()
        
        # Local panel (left)
        self.local_panel = FilePanel(panel_type="local")
        self.local_panel.path_changed.connect(self._on_local_path_changed)
        self.local_panel.file_detail.files_drag_started.connect(self._on_files_drag_started)
        self.local_panel.file_detail.files_dropped.connect(self._on_files_dropped_to_local)
        self.local_panel.folder_tree.files_dropped.connect(self._on_files_dropped_to_local)
        panels_layout.addWidget(self.local_panel, stretch=1)
        
        # Center transfer buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.addStretch()
        
        self.push_button = QPushButton("→\nPush")
        self.push_button.setToolTip(tr("Push (Local→Remote)") + " (Ctrl+P)")
        self.push_button.setMinimumWidth(60)
        self.push_button.setMinimumHeight(50)
        self.push_button.clicked.connect(self._on_push_clicked)
        buttons_layout.addWidget(self.push_button)
        
        self.pull_button = QPushButton("←\nPull")
        self.pull_button.setToolTip(tr("Pull (Remote→Local)") + " (Ctrl+Shift+P)")
        self.pull_button.setMinimumWidth(60)
        self.pull_button.setMinimumHeight(50)
        self.pull_button.clicked.connect(self._on_pull_clicked)
        buttons_layout.addWidget(self.pull_button)
        
        buttons_layout.addStretch()
        panels_layout.addLayout(buttons_layout)
        
        # Remote panel (right)
        self.remote_panel = FilePanel(panel_type="remote")
        self.remote_panel.path_changed.connect(self._on_remote_path_changed)
        self.remote_panel.file_detail.files_drag_started.connect(self._on_files_drag_started)
        self.remote_panel.file_detail.files_dropped.connect(self._on_files_dropped_to_remote)
        self.remote_panel.folder_tree.files_dropped.connect(self._on_files_dropped_to_remote)
        panels_layout.addWidget(self.remote_panel, stretch=1)
        
        # Wrap panel layout in a widget
        panels_widget = QWidget()
        panels_widget.setLayout(panels_layout)
        panels_widget.setMinimumHeight(200)  # Minimum height 200px
        main_splitter.addWidget(panels_widget)
        
        # 3. Transfer queue widget (bottom)
        self.transfer_queue = TransferQueueWidget()
        self.transfer_queue.pause_clicked.connect(self._on_pause_transfer)
        self.transfer_queue.retry_clicked.connect(self._on_retry_transfer)
        self.transfer_queue.setMinimumHeight(120)  # Minimum height 120px
        main_splitter.addWidget(self.transfer_queue)
        
        # Splitter size ratio (Console:Panel:Queue = 1:4:1)
        main_splitter.setSizes([150, 600, 150])
        
        # Add to main layout
        main_layout.addWidget(main_splitter)
        
        # Console log
        self.console.log_info(tr("UI initialized"))
    
    def _init_menubar(self) -> None:
        """Initialize menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(tr("File") + "(&F)")
        
        # Language submenu
        language_menu = file_menu.addMenu(tr("Language"))
        
        # English action
        english_action = QAction(tr("English"), self)
        english_action.triggered.connect(lambda: self._on_language_changed("en"))
        language_menu.addAction(english_action)
        
        # Korean action
        korean_action = QAction(tr("Korean"), self)
        korean_action.triggered.connect(lambda: self._on_language_changed("ko"))
        language_menu.addAction(korean_action)
        
        file_menu.addSeparator()
        
        # About action
        about_action = QAction(tr("About") + "(&A)", self)
        about_action.triggered.connect(self._show_about_dialog)
        file_menu.addAction(about_action)
        
        # Exit action
        exit_action = QAction(tr("Exit") + "(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Transfer menu
        transfer_menu = menubar.addMenu(tr("Transfer") + "(&T)")
        
        # Push action
        push_action = QAction(tr("Push (Local→Remote)"), self)
        push_action.setShortcut("Ctrl+P")
        push_action.triggered.connect(self._on_push_clicked)
        transfer_menu.addAction(push_action)
        
        # Pull action
        pull_action = QAction(tr("Pull (Remote→Local)"), self)
        pull_action.setShortcut("Ctrl+Shift+P")
        pull_action.triggered.connect(self._on_pull_clicked)
        transfer_menu.addAction(pull_action)
    
    def _init_statusbar(self) -> None:
        """Initialize status bar."""
        statusbar = self.statusBar()
        statusbar.showMessage(tr("Ready"))
    
    def _init_device_watcher(self) -> None:
        """Initialize device watcher worker."""
        self.console.log_info(tr("Device Watcher started"))
        
        # Create QThread
        self.device_thread = QThread()
        
        # Create DeviceWatcher instance
        self.device_watcher = DeviceWatcher()
        
        # Move worker to thread
        self.device_watcher.moveToThread(self.device_thread)
        
        # Connect signals
        self.device_watcher.devices_changed.connect(self._on_devices_changed)
        self.device_watcher.error_occurred.connect(self._on_device_error)
        
        # Start worker when thread starts
        self.device_thread.started.connect(self.device_watcher.start_watching)
        
        # Start thread
        self.device_thread.start()
    
    def _on_devices_changed(self, devices: list[AdbDevice]) -> None:
        """Device list changed signal handler.
        
        Args:
            devices: List of currently connected devices
        """
        if not devices:
            self.statusBar().showMessage(tr("No device connected"))
            self.console.log_warning(tr("No device connected"))
            self.remote_panel.set_device(None)
        elif len(devices) == 1:
            device = devices[0]
            model_info = f" ({device.model})" if device.model else ""
            status_msg = f"{tr('Connected device')}: {device.serial}{model_info} [{device.state}]"
            
            self.statusBar().showMessage(status_msg)
            self.console.log_info(status_msg)
            
            # Set device to remote panel
            if device.state == "device":
                self.remote_panel.set_device(device)
            else:
                self.console.log_warning(f"Device state abnormal: {device.state}")
                self.remote_panel.set_device(None)
        else:
            self.statusBar().showMessage(f"{tr('Connected device')}: {len(devices)}")
            self.console.log_info(f"{tr('Connected device')}: {len(devices)}")
            
            # Use first active device if multiple devices connected
            active_device = next((d for d in devices if d.state == "device"), None)
            if active_device:
                self.remote_panel.set_device(active_device)
                self.console.log_info(f"Using first active device: {active_device.serial}")
            else:
                self.remote_panel.set_device(None)
    
    def _on_device_error(self, error_message: str) -> None:
        """Device watcher error signal handler.
        
        Args:
            error_message: Error message
        """
        self.statusBar().showMessage(f"⚠ {error_message}", 5000)
        self.console.log_error(error_message)
    
    def _on_local_path_changed(self, path: str) -> None:
        """Local path change handler.
        
        Args:
            path: Changed local path
        """
        self.console.log_debug(f"Local path: {path}")
    
    def _on_remote_path_changed(self, path: str) -> None:
        """Remote path change handler.
        
        Args:
            path: Changed remote path
        """
        self.console.log_debug(f"Remote path: {path}")
    
    def _on_language_changed(self, language: str) -> None:
        """Language selection handler.
        
        Args:
            language: Language code ("en" or "ko")
        """
        # Save language preference
        set_config("language", language)
        set_language(language)
        
        # Show restart message
        lang_name = "English" if language == "en" else "한국어"
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        
        if language == "en":
            msg.setWindowTitle("Language Changed")
            msg.setText(f"Language changed to {lang_name}.")
            msg.setInformativeText("Please restart the application to apply changes.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        else:
            msg.setWindowTitle("언어 변경됨")
            msg.setText(f"언어가 {lang_name}(으)로 변경되었습니다.")
            msg.setInformativeText("변경사항을 적용하려면 애플리케이션을 재시작하세요.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        msg.exec()
        
        self.console.log_info(f"Language changed to {lang_name}")
    
    def _show_about_dialog(self) -> None:
        """Show about dialog."""
        about_text = """<h2>ADBCopy</h2>
<p>ADB File Explorer with FileZilla-style UI</p>
<p><b>Version:</b> 0.1.0</p>
<p><b>GitHub:</b> <a href="https://github.com/gerosyab/ADBCopy">github.com/gerosyab/ADBCopy</a></p>
<p><b>License:</b> MIT License</p>
<hr>
<p style="font-size: 10pt;">Copyright © 2025 gerosyab</p>"""
        
        QMessageBox.about(self, tr("About ADBCopy"), about_text)
    
    def _toggle_console(self) -> None:
        """Toggle console visibility."""
        if self.console.isVisible():
            self.console.hide()
            self.console.log_info("Console hidden")
        else:
            self.console.show()
            self.console.log_info("Console shown")
    
    def _init_transfer_worker(self) -> None:
        """Initialize transfer worker."""
        self.transfer_thread = QThread()
        self.transfer_worker = TransferWorker()
        self.transfer_worker.moveToThread(self.transfer_thread)
        
        # Connect signals
        self.transfer_worker.transfer_started.connect(self._on_transfer_started)
        self.transfer_worker.transfer_progress.connect(self._on_transfer_progress)
        self.transfer_worker.transfer_completed.connect(self._on_transfer_completed)
        self.transfer_worker.transfer_failed.connect(self._on_transfer_failed)
        self.transfer_worker.all_completed.connect(self._on_all_transfers_completed)
        
        self.console.log_info("Transfer worker initialized")
    
    def _on_files_drag_started(self, file_infos: list[dict]) -> None:
        """File drag start handler.
        
        Args:
            file_infos: List of dragged file information
        """
        print(f"[DEBUG] _on_files_drag_started: {len(file_infos)} files")
        for f in file_infos:
            print(f"[DEBUG]   - {f['name']} (is_dir: {f.get('is_dir', False)})")
        
        self._drag_source_files = file_infos
        self.console.log_debug(f"{len(file_infos)} files drag started")
    
    def _on_files_dropped_to_local(self, dropped_files: list) -> None:
        """File drop handler for local panel.
        
        Args:
            dropped_files: Dropped file info (unused, uses _drag_source_files instead)
        """
        print(f"[DEBUG] _on_files_dropped_to_local called")
        print(f"[DEBUG] _drag_source_files: {len(self._drag_source_files) if self._drag_source_files else 0} files")
        
        if not self._drag_source_files:
            self.console.log_warning("No dragged file information")
            return
        
        source_panel_type = self._drag_source_files[0]["panel_type"]
        print(f"[DEBUG] source_panel_type: {source_panel_type}")
        
        # Ignore if dropped to same panel
        if source_panel_type == "local":
            self.console.log_debug("Dropped to same panel (ignored)")
            self._drag_source_files = []
            return
        
        # Remote → Local
        dest_path = self.local_panel.file_detail.current_path
        if not dest_path:
            dest_path = str(Path.home())
        
        print(f"[DEBUG] dest_path: {dest_path}")
        
        # Separate files and folders
        files_only = [f for f in self._drag_source_files if not f.get("is_dir", False)]
        folders_only = [f for f in self._drag_source_files if f.get("is_dir", False)]
        
        print(f"[DEBUG] After folder filtering: {len(files_only)} files, {len(folders_only)} folders")
        
        if folders_only:
            self.console.log_warning(f"{len(folders_only)} folders skipped (folder transfer not supported)")
        
        if not files_only:
            self.console.log_warning("No transferable files")
            self._drag_source_files = []
            return
        
        device_serial = files_only[0]["device_serial"]
        print(f"[DEBUG] _add_transfer_tasks call: pull, {len(files_only)} files")
        self._add_transfer_tasks("pull", files_only, dest_path, device_serial)
        
        # Reset drag info
        self._drag_source_files = []
    
    def _on_files_dropped_to_remote(self, dropped_files: list) -> None:
        """File drop handler for remote panel.
        
        Args:
            dropped_files: Dropped file info (unused, uses _drag_source_files instead)
        """
        print(f"[DEBUG] _on_files_dropped_to_remote called")
        print(f"[DEBUG] _drag_source_files: {len(self._drag_source_files) if self._drag_source_files else 0} files")
        
        if not self._drag_source_files:
            self.console.log_warning("No dragged file information")
            return
        
        source_panel_type = self._drag_source_files[0]["panel_type"]
        print(f"[DEBUG] source_panel_type: {source_panel_type}")
        
        # Ignore if dropped to same panel
        if source_panel_type == "remote":
            self.console.log_debug("Dropped to same panel (ignored)")
            self._drag_source_files = []
            return
        
        # Local → Remote
        dest_device = self.remote_panel.file_detail.current_device
        if not dest_device:
            QMessageBox.warning(self, tr("Transfer failed"), tr("No device connected"))
            self._drag_source_files = []
            return
        
        dest_path = self.remote_panel.file_detail.current_path
        if not dest_path:
            dest_path = "/sdcard/"
        
        print(f"[DEBUG] dest_path: {dest_path}")
        
        # Separate files and folders
        files_only = [f for f in self._drag_source_files if not f.get("is_dir", False)]
        folders_only = [f for f in self._drag_source_files if f.get("is_dir", False)]
        
        print(f"[DEBUG] After folder filtering: {len(files_only)} files, {len(folders_only)} folders")
        
        if folders_only:
            self.console.log_warning(f"{len(folders_only)} folders skipped (folder transfer not supported)")
        
        if not files_only:
            self.console.log_warning("No transferable files")
            self._drag_source_files = []
            return
        
        print(f"[DEBUG] _add_transfer_tasks call: push, {len(files_only)} files")
        self._add_transfer_tasks("push", files_only, dest_path, dest_device.serial)
        
        # Reset drag info
        self._drag_source_files = []
    
    def _on_push_clicked(self) -> None:
        """Push button click handler (Local → Remote)."""
        # Get selected files from local panel
        selected_rows = set(
            item.row() 
            for item in self.local_panel.file_detail.table.selectedItems()
        )
        
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select files to transfer from local panel.")
            return
        
        # Check remote panel
        dest_device = self.remote_panel.file_detail.current_device
        if not dest_device:
            QMessageBox.warning(self, "Transfer failed", tr("No device connected"))
            return
        
        # 선택된 파일 정보 수집
        file_infos = []
        for row in selected_rows:
            name_item = self.local_panel.file_detail.table.item(row, 0)
            if not name_item:
                continue
            
            path = name_item.data(Qt.ItemDataRole.UserRole)
            is_dir = name_item.data(Qt.ItemDataRole.UserRole + 1)
            
            if is_dir:
                continue  # Exclude folders
            
            size_item = self.local_panel.file_detail.table.item(row, 1)
            size_str = size_item.text() if size_item else "0 B"
            size_bytes = self.local_panel.file_detail._parse_size(size_str)
            
            file_info = {
                "path": path,
                "name": Path(path).name,
                "size": size_bytes,
                "panel_type": "local",
                "device_serial": None,
            }
            file_infos.append(file_info)
        
        if not file_infos:
            QMessageBox.information(self, "Info", "No transferable files (folders are excluded)")
            return
        
        dest_path = self.remote_panel.file_detail.current_path or "/sdcard/"
        self._add_transfer_tasks("push", file_infos, dest_path, dest_device.serial)
    
    def _on_pull_clicked(self) -> None:
        """Pull button click handler (Remote → Local)."""
        # Get selected files from remote panel
        selected_rows = set(
            item.row() 
            for item in self.remote_panel.file_detail.table.selectedItems()
        )
        
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select files to transfer from remote panel.")
            return
        
        # Check remote panel
        dest_device = self.remote_panel.file_detail.current_device
        if not dest_device:
            QMessageBox.warning(self, "Transfer failed", tr("No device connected"))
            return
        
        # Collect selected file information
        file_infos = []
        for row in selected_rows:
            name_item = self.remote_panel.file_detail.table.item(row, 0)
            if not name_item:
                continue
            
            path = name_item.data(Qt.ItemDataRole.UserRole)
            is_dir = name_item.data(Qt.ItemDataRole.UserRole + 1)
            
            if is_dir:
                continue  # Exclude folders
            
            size_item = self.remote_panel.file_detail.table.item(row, 1)
            size_str = size_item.text() if size_item else "0 B"
            size_bytes = self.remote_panel.file_detail._parse_size(size_str)
            
            file_info = {
                "path": path,
                "name": Path(path).name,
                "size": size_bytes,
                "panel_type": "remote",
                "device_serial": dest_device.serial,
            }
            file_infos.append(file_info)
        
        if not file_infos:
            QMessageBox.information(self, "Info", "No transferable files (folders are excluded)")
            return
        
        dest_path = self.local_panel.file_detail.current_path or str(Path.home())
        self._add_transfer_tasks("pull", file_infos, dest_path, dest_device.serial)
    
    def _add_transfer_tasks(
        self,
        direction: str,
        file_infos: list[dict],
        dest_path: str,
        device_serial: str,
    ) -> None:
        """Add transfer tasks.
        
        Args:
            direction: Transfer direction ("push" or "pull")
            file_infos: List of file information
            dest_path: Destination path
            device_serial: Device serial number
        """
        print(f"[DEBUG] _add_transfer_tasks start: direction={direction}, files={len(file_infos)}")
        
        # Reset "apply to all" action
        self._overwrite_all_action = None
        
        # Batch processing settings
        BATCH_SIZE = 50  # Process 50 files per batch
        total_files = len(file_infos)
        
        # Disable sorting (performance improvement)
        self.transfer_queue.table.setSortingEnabled(False)
        
        # Add files in batches
        for i in range(0, total_files, BATCH_SIZE):
            batch = file_infos[i:i+BATCH_SIZE]
            batch_end = min(i + BATCH_SIZE, total_files)
            
            print(f"[DEBUG] Processing batch: {i+1}-{batch_end}/{total_files}")
            
            for file_info in batch:
                task_id = self._next_task_id
                self._next_task_id += 1
                
                filename = Path(file_info["path"]).name
                source_path = file_info["path"]
                
                if direction == "push":
                    destination_path = f"{dest_path.rstrip('/')}/{filename}"
                else:
                    destination_path = str(Path(dest_path) / filename)
                
                # Add to transfer queue (UI) - skip stats update
                self.transfer_queue.add_transfer(
                    task_id,
                    filename,
                    source_path,
                    destination_path,
                    skip_stats_update=True,  # Skip stats update during batch processing
                    file_size=file_info.get("size", 0),
                )
                
                # Add task to worker
                task = TransferTask(
                    task_id=task_id,
                    filename=filename,
                    source_path=source_path,
                    destination_path=destination_path,
                    direction=direction,
                    device_serial=device_serial,
                    file_size=file_info.get("size", 0),
                )
                self.transfer_worker.add_task(task)
            
            # Refresh UI between batches (prevent blocking)
            QApplication.processEvents()
        
        # Re-enable sorting
        self.transfer_queue.table.setSortingEnabled(True)
        
        # Update stats only once
        self.transfer_queue._update_status_stats()
        
        direction_text = "Upload" if direction == "push" else "Download"
        self.console.log_info(f"{total_files} files added for transfer ({direction_text})")
        
        # Start worker if not running
        print(f"[DEBUG] Thread running status: {self.transfer_thread.isRunning()}")
        
        if not self.transfer_thread.isRunning():
            print("[DEBUG] Starting transfer thread")
            
            # Disconnect existing connection and reconnect
            try:
                self.transfer_thread.started.disconnect()
            except:
                pass
            
            self.transfer_thread.started.connect(self.transfer_worker.start_transfer)
            self.transfer_thread.start()
            self.transfer_queue.enable_pause_button(True)
            self.console.log_info(tr("Transfer started"))
        else:
            print("[DEBUG] Transfer thread already running")
            self.console.log_info("Added to transfer queue (in progress)")
    
    def _on_transfer_started(self, task_id: int) -> None:
        """Transfer start signal handler.
        
        Args:
            task_id: Task ID
        """
        print(f"[DEBUG] _on_transfer_started called: task_id={task_id}")
        self.console.log_debug(f"Transfer started: Task {task_id}")
    
    def _on_transfer_progress(self, task_id: int, progress: int, speed: str) -> None:
        """Transfer progress signal handler.
        
        Args:
            task_id: Task ID
            progress: Progress (0-100)
            speed: Speed string
        """
        print(f"[DEBUG] _on_transfer_progress called: task_id={task_id}, progress={progress}, speed={speed}")
        self.transfer_queue.update_progress_by_task_id(task_id, progress, speed=speed)
    
    def _on_transfer_completed(self, task_id: int) -> None:
        """Transfer completed signal handler.
        
        Args:
            task_id: Task ID
        """
        print(f"[DEBUG] _on_transfer_completed called: task_id={task_id}")
        self.console.log_debug(f"Transfer completed: Task {task_id}")
        self.transfer_queue.update_progress_by_task_id(task_id, 100)
        
        # No refresh on individual completion (performance)
    
    def _on_transfer_failed(self, task_id: int, error_message: str) -> None:
        """Transfer failed signal handler.
        
        Args:
            task_id: Task ID
            error_message: Error message
        """
        print(f"[DEBUG] _on_transfer_failed called: task_id={task_id}, error={error_message}")
        self.console.log_error(f"Transfer failed (Task {task_id}): {error_message}")
        self.transfer_queue.mark_failed_by_task_id(task_id, error_message)
    
    def _on_all_transfers_completed(self) -> None:
        """All transfers completed signal handler."""
        self.console.log_info(tr("All transfers completed"))
        self.transfer_queue.enable_pause_button(False)
        
        # Clean up thread (call quit only for reuse)
        if self.transfer_thread.isRunning():
            self.transfer_thread.quit()
            self.transfer_thread.wait()
        
        # Final refresh
        self._refresh_panels_after_transfer()
    
    def _on_pause_transfer(self) -> None:
        """Transfer pause/resume handler."""
        if self.transfer_queue._paused:
            self.transfer_worker.pause()
            self.console.log_info("Transfer paused")
        else:
            self.transfer_worker.resume()
            self.console.log_info("Transfer resumed")
    
    def _on_retry_transfer(self) -> None:
        """Failed transfer retry handler."""
        if not self.remote_panel.file_detail.current_device:
            self.console.log_error(tr("No device connected"))
            return
        
        device_serial = self.remote_panel.file_detail.current_device.serial
        retry_count = 0
        
        # Collect failed tasks
        failed_tasks = []
        table = self.transfer_queue.table
        
        for row in range(table.rowCount()):
            status_item = table.item(row, 0)
            if not status_item or status_item.text() != tr("✗ Failed"):
                continue
            
            # Collect file information
            name_item = table.item(row, 1)
            source_item = table.item(row, 2)
            dest_item = table.item(row, 3)
            
            if not (name_item and source_item and dest_item):
                continue
            
            filename = name_item.text()
            source_path = source_item.text()
            dest_path = dest_item.text()
            
            # Determine direction (Windows path vs Unix path)
            if source_path.startswith("/"):
                # Unix path → Remote is source → pull
                direction = "pull"
            else:
                # Windows path → Local is source → push
                direction = "push"
            
            # Get file size
            file_size = 0
            try:
                if direction == "push":
                    # Local file size
                    local_file = Path(source_path)
                    if local_file.exists():
                        file_size = local_file.stat().st_size
                else:
                    # Remote file size (omitted, set to 0)
                    file_size = 0
            except Exception:
                pass
            
            failed_tasks.append({
                "row": row,
                "filename": filename,
                "source_path": source_path,
                "dest_path": dest_path,
                "direction": direction,
                "file_size": file_size,
            })
        
        if not failed_tasks:
            self.console.log_info("No failed tasks to retry")
            return
        
        # Remove failed rows from table (reverse order)
        for task in reversed(failed_tasks):
            table.removeRow(task["row"])
        
        # Update stats
        self.transfer_queue._update_status_stats()
        
        # Add retry tasks
        for task in failed_tasks:
            task_id = self._next_task_id
            self._next_task_id += 1
            
            # Add to transfer queue
            self.transfer_queue.add_transfer(
                task_id,
                task["filename"],
                task["source_path"],
                task["dest_path"],
                file_size=task["file_size"],
            )
            
            # Add task to worker
            transfer_task = TransferTask(
                task_id=task_id,
                filename=task["filename"],
                source_path=task["source_path"],
                destination_path=task["dest_path"],
                direction=task["direction"],
                device_serial=device_serial,
                file_size=task["file_size"],
            )
            self.transfer_worker.add_task(transfer_task)
            retry_count += 1
        
        self.console.log_info(f"Retrying {retry_count} failed tasks...")
        
        # Start worker if not running
        if not self.transfer_thread.isRunning():
            try:
                self.transfer_thread.started.disconnect()
            except:
                pass
            
            self.transfer_thread.started.connect(self.transfer_worker.start_transfer)
            self.transfer_thread.start()
            self.transfer_queue.enable_pause_button(True)
    
    def _check_overwrite(
        self,
        filename: str,
        source_size: int,
        dest_size: int,
    ) -> int:
        """Show file overwrite confirmation dialog.
        
        Args:
            filename: Filename
            source_size: Source file size
            dest_size: Destination file size
            
        Returns:
            User choice (OVERWRITE, SKIP, RENAME, CANCEL)
        """
        # Return saved action if "apply to all" is enabled
        if self._overwrite_all_action is not None:
            return self._overwrite_all_action
        
        # Show dialog
        dialog = OverwriteDialog(filename, source_size, dest_size, self)
        result = dialog.exec()
        
        # Save action if "apply to all" is checked
        if dialog.apply_to_all:
            self._overwrite_all_action = result
        
        return result
    
    def _get_unique_name(
        self,
        device_serial: str,
        dest_path: str,
        filename: str,
    ) -> str:
        """Generate unique filename (for remote).
        
        Args:
            device_serial: Device serial number
            dest_path: Destination path
            filename: Filename
            
        Returns:
            Unique full path
        """
        base_name = Path(filename).stem
        ext = Path(filename).suffix
        counter = 1
        
        while True:
            new_name = f"{base_name}_{counter}{ext}"
            new_path = f"{dest_path.rstrip('/')}/{new_name}"
            
            if not self.adb_manager.file_exists(device_serial, new_path):
                return new_path
            
            counter += 1
            
            # Prevent infinite loop
            if counter > 100:
                return new_path
    
    def _refresh_panels_after_transfer(self) -> None:
        """Refresh panels after transfer completion."""
        # Refresh local panel
        if self.local_panel.file_detail.current_path:
            self.local_panel.file_detail.load_path(
                self.local_panel.file_detail.current_path
            )
        
        # Refresh remote panel
        if self.remote_panel.file_detail.current_path:
            self.remote_panel.file_detail.load_path(
                self.remote_panel.file_detail.current_path
            )
    
    def closeEvent(self, event) -> None:
        """Window close event handler.
        
        Args:
            event: QCloseEvent
        """
        self.console.log_info("Closing application...")
        
        # Clean up transfer worker
        if hasattr(self, "transfer_worker"):
            self.transfer_worker.stop()
        
        if hasattr(self, "transfer_thread") and self.transfer_thread.isRunning():
            self.transfer_thread.quit()
            self.transfer_thread.wait(2000)
        
        # Clean up device watcher
        if hasattr(self, "device_watcher"):
            self.device_watcher.stop_watching()
        
        if hasattr(self, "device_thread"):
            self.device_thread.quit()
            self.device_thread.wait(2000)
        
        event.accept()
