"""File detail list widget module.

Displays file/folder list of selected folder in a table.
"""

from pathlib import Path
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData
from PyQt6.QtGui import QDrag, QAction
from PyQt6.QtWidgets import (
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from adb_copy.core.adb_manager import AdbDevice, AdbManager
from adb_copy.workers.file_list_worker import FileListWorker, RemoteFileInfo
from adb_copy.i18n import tr


class FileDetailWidget(QWidget):
    """File detail list widget class.
    
    Displays filename, size, permissions, date, etc. in a table.
    
    Signals:
        folder_double_clicked: Emitted on folder double-click (str: folder path)
        files_drag_started: Emitted when file drag starts (list[dict]: file info list)
        files_dropped: Emitted when files are dropped (list[dict]: file info)
    """
    
    folder_double_clicked = pyqtSignal(str)
    files_drag_started = pyqtSignal(list)  # list of file info dicts
    files_dropped = pyqtSignal(list)
    refresh_requested = pyqtSignal()  # Refresh request
    
    def __init__(self, panel_type: str = "local") -> None:
        """Initialize FileDetailWidget instance.
        
        Args:
            panel_type: Panel type. "local" or "remote"
        """
        super().__init__()
        self.panel_type = panel_type
        self.current_path = ""
        self.current_device: AdbDevice | None = None
        self.adb_manager = AdbManager() if panel_type == "remote" else None
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Table widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Size", "Permissions", "Type"])
        
        # Column size adjustment
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Row selection mode
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection  # Allow multiple selection
        )
        self.table.setAlternatingRowColors(True)
        
        # Enable drag
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDropIndicatorShown(True)
        self.table.setDefaultDropAction(Qt.DropAction.CopyAction)
        
        # Double-click event
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        
        # Override drag/drop events
        self.table.startDrag = self._start_drag
        self.table.dragEnterEvent = self._drag_enter_event
        self.table.dragMoveEvent = self._drag_move_event
        self.table.dropEvent = self._drop_event
        
        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Selection change event
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
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
        
        # Status bar (bottom)
        self.status_label = QLabel("0 items")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 3px 5px;
                border-top: 1px solid #ccc;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.status_label)
    
    def set_device(self, device: AdbDevice | None) -> None:
        """Set connected device for remote panel.
        
        Args:
            device: Connected ADB device
        """
        if self.panel_type != "remote":
            return
        
        self.current_device = device
    
    def load_path(self, path: str) -> None:
        """Load file list of specified path.
        
        Args:
            path: Path to load
        """
        print(f"[DEBUG] load_path called: {path}, panel={self.panel_type}")
        self.current_path = path
        
        if self.panel_type == "local":
            self._load_local_files(path)
        else:
            self._load_remote_files(path)
    
    def _load_local_files(self, path: str) -> None:
        """Load file list of local path.
        
        Args:
            path: Local path to load
        """
        try:
            path_obj = Path(path)
            
            if not path_obj.exists() or not path_obj.is_dir():
                self._show_error("Invalid path.")
                return
            
            # Temporarily disable sorting (performance improvement)
            self.table.setSortingEnabled(False)
            
            # Initialize table
            self.table.setRowCount(0)
            
            # Add parent folder item (..)
            if path_obj.parent != path_obj:  # If not root
                row = 0
                self.table.insertRow(row)
                
                parent_item = QTableWidgetItem("📁 ..")
                parent_item.setData(Qt.ItemDataRole.UserRole, str(path_obj.parent))
                parent_item.setData(Qt.ItemDataRole.UserRole + 1, True)  # is_dir
                self.table.setItem(row, 0, parent_item)
                
                self.table.setItem(row, 1, QTableWidgetItem(""))
                self.table.setItem(row, 2, QTableWidgetItem(""))
                self.table.setItem(row, 3, QTableWidgetItem("Parent"))
            
            # Get file list
            items = sorted(
                path_obj.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
            
            for item in items:
                is_dir = item.is_dir()
                size = 0 if is_dir else item.stat().st_size
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Name
                name_item = QTableWidgetItem(
                    f"📁 {item.name}" if is_dir else item.name
                )
                name_item.setData(Qt.ItemDataRole.UserRole, str(item))
                name_item.setData(Qt.ItemDataRole.UserRole + 1, is_dir)
                self.table.setItem(row, 0, name_item)
                
                # Size
                size_item = QTableWidgetItem(self._format_size(size))
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 1, size_item)
                
                # Permissions
                perm_item = QTableWidgetItem("Folder" if is_dir else "File")
                self.table.setItem(row, 2, perm_item)
                
                # Type
                type_item = QTableWidgetItem(
                    "Folder" if is_dir else item.suffix or "-"
                )
                self.table.setItem(row, 3, type_item)
            
            # Update status bar
            self._update_status_bar()
            
            # Re-enable sorting
            self.table.setSortingEnabled(True)
                
        except PermissionError:
            self._show_error("Permission denied.")
        except Exception as e:
            self._show_error(f"Load failed: {str(e)}")
    
    def _load_remote_files(self, path: str) -> None:
        """Load file list of remote path.
        
        Args:
            path: Remote path to load
        """
        if not self.current_device:
            # Don't show error, just keep empty table
            self.table.setRowCount(0)
            return
        
        # Clean up existing thread if any
        if hasattr(self, '_file_list_thread') and self._file_list_thread is not None:
            if self._file_list_thread.isRunning():
                print("[DEBUG] Terminating existing thread...")
                self._file_list_thread.quit()
                self._file_list_thread.wait(1000)
        
        # Show loading indicator
        self.table.setRowCount(1)
        loading_item = QTableWidgetItem("Loading...")
        self.table.setItem(0, 0, loading_item)
        
        # Asynchronous load with worker
        self._file_list_thread = QThread()
        worker = FileListWorker()
        worker.moveToThread(self._file_list_thread)
        
        worker.files_loaded.connect(self._on_remote_files_loaded)
        worker.error_occurred.connect(self._show_error)
        
        # Clean up thread after completion
        def cleanup_thread():
            if self._file_list_thread:
                self._file_list_thread.quit()
                self._file_list_thread.wait()
                print("[DEBUG] File list thread cleaned up")
        
        worker.files_loaded.connect(cleanup_thread)
        worker.error_occurred.connect(cleanup_thread)
        
        device_serial = self.current_device.serial
        self._file_list_thread.started.connect(lambda: worker.list_files(device_serial, path))
        self._file_list_thread.start()
    
    def _on_remote_files_loaded(self, files: list[RemoteFileInfo]) -> None:
        """Remote file list load completion handler.
        
        Args:
            files: File list
        """
        # Update current_path (extract from first file's path)
        if files and not self.current_path:
            first_file_path = files[0].path
            self.current_path = "/".join(first_file_path.rstrip("/").split("/")[:-1]) or "/"
        
        # Temporarily disable sorting (performance improvement)
        self.table.setSortingEnabled(False)
        
        self.table.setRowCount(0)
        
        # Add parent folder item (..)
        if self.current_path and self.current_path != "/":
            row = 0
            self.table.insertRow(row)
            
            parent_item = QTableWidgetItem("📁 ..")
            parent_path = "/".join(self.current_path.rstrip("/").split("/")[:-1]) or "/"
            parent_item.setData(Qt.ItemDataRole.UserRole, parent_path)
            parent_item.setData(Qt.ItemDataRole.UserRole + 1, True)  # is_dir
            self.table.setItem(row, 0, parent_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(""))
            self.table.setItem(row, 2, QTableWidgetItem(""))
            self.table.setItem(row, 3, QTableWidgetItem("Parent"))
        
        for file_info in files:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(
                f"📁 {file_info.name}" if file_info.is_dir else file_info.name
            )
            name_item.setData(Qt.ItemDataRole.UserRole, file_info.path)
            name_item.setData(Qt.ItemDataRole.UserRole + 1, file_info.is_dir)
            self.table.setItem(row, 0, name_item)
            
            # Size
            size_item = QTableWidgetItem(self._format_size(file_info.size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)
            
            # Permissions
            perm_item = QTableWidgetItem(file_info.permissions)
            self.table.setItem(row, 2, perm_item)
            
            # Type
            type_item = QTableWidgetItem(
                "Folder" if file_info.is_dir else Path(file_info.name).suffix or "-"
            )
            self.table.setItem(row, 3, type_item)
        
        # Update status bar
        self._update_status_bar()
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
    
    def _on_cell_double_clicked(self, row: int, column: int) -> None:
        """Cell double-click handler.
        
        Args:
            row: Row index
            column: Column index
        """
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        
        path = name_item.data(Qt.ItemDataRole.UserRole)
        is_dir = name_item.data(Qt.ItemDataRole.UserRole + 1)
        
        # Enter if folder (or .. item)
        if is_dir:
            print(f"[DEBUG] Folder double-clicked: {path}")
            self.folder_double_clicked.emit(path)
    
    def _format_size(self, size: int) -> str:
        """Format file size.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size == 0:
            return ""
        
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        
        return f"{size:.1f} PB"
    
    def _show_error(self, message: str) -> None:
        """Display error message.
        
        Args:
            message: Error message
        """
        self.table.setRowCount(1)
        error_item = QTableWidgetItem(f"⚠ {message}")
        self.table.setItem(0, 0, error_item)
    
    def _start_drag(self, supported_actions: Qt.DropAction) -> None:
        """Handle drag start event.
        
        Args:
            supported_actions: Supported drop actions
        """
        print(f"[DEBUG] _start_drag called: panel_type={self.panel_type}")
        
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            print("[DEBUG] No rows selected")
            return
        
        print(f"[DEBUG] Number of selected rows: {len(selected_rows)}")
        
        # Collect selected file info
        file_infos = []
        for row in selected_rows:
            name_item = self.table.item(row, 0)
            if not name_item:
                continue
            
            path = name_item.data(Qt.ItemDataRole.UserRole)
            is_dir = name_item.data(Qt.ItemDataRole.UserRole + 1)
            
            print(f"[DEBUG] Item: path={path}, is_dir={is_dir}")
            
            # Exclude .. (parent folder) item
            if path and ".." in str(path):
                print(f"[DEBUG] Excluding parent folder item")
                continue
            
            # Get size
            size_item = self.table.item(row, 1)
            size_str = size_item.text() if size_item else "0 B"
            size_bytes = self._parse_size(size_str) if not is_dir else 0
            
            file_info = {
                "path": path,
                "name": Path(path).name if isinstance(path, str) else path,
                "size": size_bytes,
                "is_dir": is_dir,
                "panel_type": self.panel_type,
                "device_serial": self.current_device.serial if self.current_device else None,
            }
            file_infos.append(file_info)
        
        if not file_infos:
            print("[DEBUG] No file info (all folders?)")
            return
        
        print(f"[DEBUG] Drag started: {len(file_infos)} items")
        
        # Emit signal
        self.files_drag_started.emit(file_infos)
        
        # Start drag
        drag = QDrag(self.table)
        mime_data = QMimeData()
        
        # Encode file paths as text
        paths_text = "\n".join(str(f["path"]) for f in file_infos)
        mime_data.setText(paths_text)
        
        # Add application/x-adbcopy-files type (for our app only)
        mime_data.setData("application/x-adbcopy-files", paths_text.encode())
        
        drag.setMimeData(mime_data)
        
        print(f"[DEBUG] Before drag.exec call: supported_actions={supported_actions}")
        result = drag.exec(supported_actions)
        print(f"[DEBUG] drag.exec result: {result}")
    
    def _parse_size(self, size_str: str) -> int:
        """Convert size string to bytes.
        
        Args:
            size_str: Size string (e.g. "1.2 MB")
            
        Returns:
            Size in bytes
        """
        if not size_str or size_str == "":
            return 0
        
        try:
            parts = size_str.split()
            if len(parts) != 2:
                return 0
            
            value = float(parts[0])
            unit = parts[1].upper()
            
            units = {
                "B": 1,
                "KB": 1024,
                "MB": 1024 ** 2,
                "GB": 1024 ** 3,
                "TB": 1024 ** 4,
            }
            
            return int(value * units.get(unit, 1))
        except (ValueError, IndexError):
            return 0
    
    def _drag_enter_event(self, event) -> None:
        """Drag enter event handler.
        
        Args:
            event: QDragEnterEvent
        """
        print(f"[DEBUG] file_detail._drag_enter_event: panel_type={self.panel_type}")
        print(f"[DEBUG] MIME formats: {event.mimeData().formats()}")
        
        # Check if drag started from our app
        if event.mimeData().hasFormat("application/x-adbcopy-files"):
            print("[DEBUG] application/x-adbcopy-files format detected - accept")
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        elif event.mimeData().hasText():
            print("[DEBUG] text format detected - accept")
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            print("[DEBUG] unsupported format - ignore")
    
    def _drag_move_event(self, event) -> None:
        """Drag move event handler.
        
        Args:
            event: QDragMoveEvent
        """
        print(f"[DEBUG] file_detail._drag_move_event: panel_type={self.panel_type}")
        
        # Same logic as dragEnterEvent
        if event.mimeData().hasFormat("application/x-adbcopy-files") or event.mimeData().hasText():
            print("[DEBUG] dragMove accept")
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            print("[DEBUG] dragMove ignore")
            event.ignore()
    
    def _drop_event(self, event) -> None:
        """Drop event handler.
        
        Args:
            event: QDropEvent
        """
        print(f"[DEBUG] file_detail._drop_event: panel_type={self.panel_type}")
        
        if event.mimeData().hasFormat("application/x-adbcopy-files") or event.mimeData().hasText():
            print("[DEBUG] Drop allowed")
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            # Notify drop (actual file info is managed in main_window)
            self.files_dropped.emit([])
            print("[DEBUG] files_dropped signal emitted")
        else:
            print("[DEBUG] Drop rejected")
    
    def _show_context_menu(self, position) -> None:
        """Display context menu.
        
        Args:
            position: Mouse position
        """
        menu = QMenu(self)
        
        # Check selected items
        selected_rows = set(item.row() for item in self.table.selectedItems())
        
        if self.panel_type == "remote" and self.current_device:
            # Remote panel menu
            if selected_rows:
                delete_action = QAction(tr("Delete"), self)
                delete_action.triggered.connect(self._on_delete_selected)
                menu.addAction(delete_action)
                
                if len(selected_rows) == 1:
                    rename_action = QAction(tr("Rename"), self)
                    rename_action.triggered.connect(self._on_rename_selected)
                    menu.addAction(rename_action)
                
                menu.addSeparator()
            
            new_folder_action = QAction(tr("New Folder"), self)
            new_folder_action.triggered.connect(self._on_create_folder)
            menu.addAction(new_folder_action)
            
        elif self.panel_type == "local":
            # Local panel menu (simple version)
            if len(selected_rows) == 1:
                rename_action = QAction(tr("Rename"), self)
                rename_action.triggered.connect(self._on_rename_local)
                menu.addAction(rename_action)
        
        menu.addSeparator()
        refresh_action = QAction(tr("Refresh"), self)
        refresh_action.triggered.connect(self._on_refresh)
        menu.addAction(refresh_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def _on_delete_selected(self) -> None:
        """Delete selected files/folders handler."""
        if not self.current_device:
            return
        
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            tr("Confirm Delete"),
            tr("Delete {0} item(s)?").format(len(selected_rows)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Execute delete
        for row in selected_rows:
            name_item = self.table.item(row, 0)
            if not name_item:
                continue
            
            path = name_item.data(Qt.ItemDataRole.UserRole)
            is_dir = name_item.data(Qt.ItemDataRole.UserRole + 1)
            
            try:
                self.adb_manager.delete_file(
                    self.current_device.serial,
                    path,
                    is_dir=is_dir,
                )
            except Exception as e:
                QMessageBox.warning(self, tr("Delete Failed"), f"{path}\n\n{str(e)}")
        
        # Refresh
        self.refresh_requested.emit()
    
    def _on_rename_selected(self) -> None:
        """Rename selected item handler."""
        if not self.current_device:
            return
        
        selected_rows = list(set(item.row() for item in self.table.selectedItems()))
        if not selected_rows:
            return
        
        row = selected_rows[0]
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        
        old_path = name_item.data(Qt.ItemDataRole.UserRole)
        old_name = Path(old_path).name
        
        # New name input dialog
        new_name, ok = QInputDialog.getText(
            self,
            tr("Rename"),
            tr("New name:"),
            text=old_name,
        )
        
        if not ok or not new_name or new_name == old_name:
            return
        
        # Create new path
        parent_path = "/".join(old_path.rstrip("/").split("/")[:-1])
        new_path = f"{parent_path}/{new_name}"
        
        try:
            self.adb_manager.rename_file(
                self.current_device.serial,
                old_path,
                new_path,
            )
            # Refresh
            self.refresh_requested.emit()
        except Exception as e:
            QMessageBox.warning(self, tr("Rename Failed"), str(e))
    
    def _on_create_folder(self) -> None:
        """New folder creation handler."""
        if not self.current_device or not self.current_path:
            return
        
        # Folder name input dialog
        folder_name, ok = QInputDialog.getText(
            self,
            tr("New Folder"),
            tr("Folder name:"),
        )
        
        if not ok or not folder_name:
            return
        
        # New folder path
        new_folder_path = f"{self.current_path.rstrip('/')}/{folder_name}"
        
        try:
            self.adb_manager.create_directory(
                self.current_device.serial,
                new_folder_path,
            )
            # Refresh
            self.refresh_requested.emit()
        except Exception as e:
            QMessageBox.warning(self, tr("Folder Creation Failed"), str(e))
    
    def _on_rename_local(self) -> None:
        """Local file rename handler."""
        selected_rows = list(set(item.row() for item in self.table.selectedItems()))
        if not selected_rows:
            return
        
        row = selected_rows[0]
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        
        old_path = Path(name_item.data(Qt.ItemDataRole.UserRole))
        old_name = old_path.name
        
        # New name input dialog
        new_name, ok = QInputDialog.getText(
            self,
            tr("Rename"),
            tr("New name:"),
            text=old_name,
        )
        
        if not ok or not new_name or new_name == old_name:
            return
        
        # Create new path
        new_path = old_path.parent / new_name
        
        try:
            old_path.rename(new_path)
            # Refresh
            self.refresh_requested.emit()
        except Exception as e:
            QMessageBox.warning(self, tr("Rename Failed"), str(e))
    
    def _on_refresh(self) -> None:
        """Refresh handler."""
        self.refresh_requested.emit()
    
    def _on_selection_changed(self) -> None:
        """Selection change handler."""
        self._update_status_bar()
    
    def _update_status_bar(self) -> None:
        """Update status bar."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        
        if not selected_rows:
            # No selection - show total statistics
            total_items = self.table.rowCount()
            total_files = 0
            total_dirs = 0
            total_size = 0
            
            for row in range(total_items):
                name_item = self.table.item(row, 0)
                if not name_item:
                    continue
                
                is_dir = name_item.data(Qt.ItemDataRole.UserRole + 1)
                
                # Exclude .. item
                if name_item.text() == "📁 ..":
                    continue
                
                if is_dir:
                    total_dirs += 1
                else:
                    total_files += 1
                    size_item = self.table.item(row, 1)
                    if size_item:
                        total_size += self._parse_size(size_item.text())
            
            # Generate status bar text
            parts = []
            if total_files > 0:
                parts.append(tr("{0} file(s)").format(total_files))
            if total_dirs > 0:
                parts.append(tr("{0} dir(s)").format(total_dirs))
            if total_size > 0:
                parts.append(tr("Total size: {0}").format(self._format_size(total_size)))
            
            status_text = ", ".join(parts) if parts else tr("0 items")
            self.status_label.setText(status_text)
        else:
            # Selected items statistics
            selected_files = 0
            selected_dirs = 0
            selected_size = 0
            
            for row in selected_rows:
                name_item = self.table.item(row, 0)
                if not name_item:
                    continue
                
                is_dir = name_item.data(Qt.ItemDataRole.UserRole + 1)
                
                # Exclude .. item
                if name_item.text() == "📁 ..":
                    continue
                
                if is_dir:
                    selected_dirs += 1
                else:
                    selected_files += 1
                    size_item = self.table.item(row, 1)
                    if size_item:
                        selected_size += self._parse_size(size_item.text())
            
            # Generate status bar text
            parts = []
            if selected_files > 0:
                parts.append(tr("{0} file(s) selected").format(selected_files))
            if selected_dirs > 0:
                parts.append(tr("{0} dir(s) selected").format(selected_dirs))
            if selected_size > 0:
                parts.append(tr("Total size: {0}").format(self._format_size(selected_size)))
            
            status_text = ", ".join(parts) if parts else tr("0 selected")
            self.status_label.setText(status_text)

