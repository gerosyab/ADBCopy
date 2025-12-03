"""Folder tree widget module.

Displays hierarchical folder tree structure.
"""

import os
import string
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from adb_copy.core.adb_manager import AdbDevice, AdbManager
from adb_copy.workers.file_list_worker import FileListWorker, RemoteFileInfo
from adb_copy.i18n import tr


class FolderTreeWidget(QWidget):
    """Folder tree widget class.
    
    Displays folder hierarchy of local or remote file system as a tree.
    
    Signals:
        folder_selected: Emitted when folder is selected (str: folder path)
        files_dropped: Emitted when files are dropped (list[dict]: file info)
    """
    
    folder_selected = pyqtSignal(str)
    files_dropped = pyqtSignal(list)
    
    def __init__(self, panel_type: str = "local") -> None:
        """Initialize FolderTreeWidget instance.
        
        Args:
            panel_type: Panel type. "local" or "remote"
        """
        super().__init__()
        self.panel_type = panel_type
        self.current_device: AdbDevice | None = None
        self._previous_path = ""
        
        # Navigation history
        self._history_stack = []  # List of visited paths
        self._history_index = -1  # Current position in history
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Path input area with navigation buttons
        path_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("◀")
        self.back_button.setMaximumWidth(30)
        self.back_button.setToolTip(tr("Back"))
        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_button.setEnabled(False)
        path_layout.addWidget(self.back_button)
        
        # Forward button
        self.forward_button = QPushButton("▶")
        self.forward_button.setMaximumWidth(30)
        self.forward_button.setToolTip(tr("Forward"))
        self.forward_button.clicked.connect(self._on_forward_clicked)
        self.forward_button.setEnabled(False)
        path_layout.addWidget(self.forward_button)
        
        # Path input
        self.path_edit = QLineEdit()
        placeholder = tr("Local path...") if self.panel_type == "local" else "/"
        self.path_edit.setPlaceholderText(placeholder)
        self.path_edit.returnPressed.connect(self._on_path_entered)
        path_layout.addWidget(self.path_edit)
        
        # Go button
        go_button = QPushButton(tr("Go"))
        go_button.clicked.connect(self._on_path_entered)
        go_button.setMaximumWidth(50)
        path_layout.addWidget(go_button)
        
        layout.addLayout(path_layout)
        
        # Folder tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        self.tree_widget.itemExpanded.connect(self._on_item_expanded)
        
        # Enable drop
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.dragEnterEvent = self._drag_enter_event
        self.tree_widget.dragMoveEvent = self._drag_move_event
        self.tree_widget.dropEvent = self._drop_event
        
        # Improve hover/selection colors
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                selection-background-color: #A8D3FF;  /* Light blue */
                selection-color: #000000;  /* Black text */
            }
            QTreeWidget::item:hover {
                background-color: #E8E8E8;  /* Light gray */
            }
            QTreeWidget::item:selected {
                background-color: #A8D3FF;  /* Light blue */
                color: #000000;  /* Black text */
            }
        """)
        
        layout.addWidget(self.tree_widget)
        
        # Set initial path
        if self.panel_type == "local":
            self._load_windows_drives()
        else:
            self.path_edit.setText("/")
    
    def set_device(self, device: AdbDevice | None) -> None:
        """Set connected device for remote panel.
        
        Args:
            device: Connected ADB device
        """
        if self.panel_type != "remote":
            return
        
        self.current_device = device
        
        if device:
            self._load_remote_root("/sdcard/")
        else:
            self.tree_widget.clear()
            self.path_edit.clear()
    
    def _on_path_entered(self) -> None:
        """Called when go button is clicked after path input."""
        path = self.path_edit.text().strip()
        if not path:
            return
        
        # Normalize path (ensure consistent slash handling)
        if self.panel_type == "remote":
            # For remote paths, ensure it doesn't end with / (unless it's root)
            if path != "/" and path.endswith("/"):
                path = path.rstrip("/")
        else:
            # For local paths, normalize using Path
            path = str(Path(path))
        
        # Save current path (for recovery on failure)
        previous_path = self.path_edit.text()
        
        if self.panel_type == "local":
            if not Path(path).exists():
                QMessageBox.warning(self, tr("Path error"), tr("Path does not exist:\n{0}").format(path))
                self.path_edit.setText(previous_path)
                return
            # Navigate to path and expand tree
            self._add_to_history(path)
            self.expand_and_select_path(path)  # Expand tree to show path
            self.folder_selected.emit(path)
        else:
            # Remote path - navigate and expand tree
            self._previous_path = previous_path
            self._add_to_history(path)
            self.expand_and_select_path(path)  # Expand tree to show path
            self.folder_selected.emit(path)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Called when tree item is clicked.
        
        Args:
            item: Clicked item
            column: Column index
        """
        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Virtual nodes like "My PC" are None
        if folder_path is None:
            return
        
        if folder_path:
            self._add_to_history(folder_path)
            self.folder_selected.emit(folder_path)
    
    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Called when tree item is expanded.
        
        Args:
            item: Expanded item
        """
        # Load actual contents if child is placeholder
        if item.childCount() == 1:
            child = item.child(0)
            if child.text(0) == "...":
                folder_path = item.data(0, Qt.ItemDataRole.UserRole)
                item.removeChild(child)
                
                if self.panel_type == "local":
                    self._load_local_children(item, folder_path)
                else:
                    self._load_remote_children(item, folder_path)
    
    def _load_windows_drives(self) -> None:
        """Load Windows drives and special folders."""
        self.tree_widget.clear()
        
        # My PC root node
        my_pc_item = QTreeWidgetItem()
        my_pc_item.setText(0, "💻 My PC")
        my_pc_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self.tree_widget.addTopLevelItem(my_pc_item)
        
        # Special folders
        home_path = Path.home()
        
        special_folders = [
            ("📁 Desktop", home_path / "Desktop"),
            ("📁 Documents", home_path / "Documents"),
            ("📁 Downloads", home_path / "Downloads"),
            ("📁 Pictures", home_path / "Pictures"),
            ("📁 Music", home_path / "Music"),
            ("📁 Videos", home_path / "Videos"),
        ]
        
        for icon_name, folder_path in special_folders:
            if folder_path.exists():
                item = QTreeWidgetItem()
                item.setText(0, icon_name)
                item.setData(0, Qt.ItemDataRole.UserRole, str(folder_path))
                
                # Add placeholder if has subfolders
                try:
                    if any(p.is_dir() for p in folder_path.iterdir()):
                        placeholder = QTreeWidgetItem()
                        placeholder.setText(0, "...")
                        item.addChild(placeholder)
                except PermissionError:
                    pass
                
                my_pc_item.addChild(item)
        
        # Drives (C:\, D:\, ...)
        for drive_letter in string.ascii_uppercase:
            drive_path = Path(f"{drive_letter}:\\")
            if drive_path.exists():
                item = QTreeWidgetItem()
                item.setText(0, f"💾 {drive_letter}:\\")
                item.setData(0, Qt.ItemDataRole.UserRole, str(drive_path))
                
                # Placeholder
                placeholder = QTreeWidgetItem()
                placeholder.setText(0, "...")
                item.addChild(placeholder)
                
                my_pc_item.addChild(item)
        
        my_pc_item.setExpanded(True)
        
        # Select Documents folder by default
        documents_path = home_path / "Documents"
        if documents_path.exists():
            self.folder_selected.emit(str(documents_path))
            self.path_edit.setText(str(documents_path))
    
    def _load_local_root(self, root_path: str) -> None:
        """Load local root path (called from path input).
        
        Args:
            root_path: Root path
        """
        # Update path input
        self.path_edit.setText(root_path)
        
        # Emit folder selected signal (update file list)
        self.folder_selected.emit(root_path)
    
    def _load_local_children(self, parent_item: QTreeWidgetItem, parent_path: str) -> None:
        """Load subfolders of local folder.
        
        Args:
            parent_item: Parent tree item
            parent_path: Parent path
        """
        try:
            path_obj = Path(parent_path)
            subfolders = sorted([p for p in path_obj.iterdir() if p.is_dir()], 
                              key=lambda p: p.name.lower())
            
            for folder in subfolders:
                # Exclude hidden folders (optional)
                if folder.name.startswith("."):
                    continue
                
                item = QTreeWidgetItem()
                item.setText(0, f"📁 {folder.name}")
                item.setData(0, Qt.ItemDataRole.UserRole, str(folder))
                
                # Check for subfolders (add placeholder)
                try:
                    if any(p.is_dir() for p in folder.iterdir()):
                        placeholder = QTreeWidgetItem()
                        placeholder.setText(0, "...")
                        item.addChild(placeholder)
                except PermissionError:
                    pass
                
                parent_item.addChild(item)
                
        except PermissionError:
            error_item = QTreeWidgetItem()
            error_item.setText(0, "⚠ Permission denied")
            parent_item.addChild(error_item)
    
    def _load_remote_root(self, root_path: str) -> None:
        """Load remote root path.
        
        Args:
            root_path: Root path
        """
        if not self.current_device:
            return
        
        self.tree_widget.clear()
        self.path_edit.setText(root_path)
        
        root_item = QTreeWidgetItem()
        root_item.setText(0, f"📁 {root_path}")
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_path)
        
        self.tree_widget.addTopLevelItem(root_item)
        self._load_remote_children(root_item, root_path)
        root_item.setExpanded(True)
        
        self.folder_selected.emit(root_path)
    
    def _load_remote_children(
        self,
        parent_item: QTreeWidgetItem,
        parent_path: str,
    ) -> None:
        """Load subfolders of remote folder.
        
        Args:
            parent_item: Parent tree item
            parent_path: Parent path
        """
        if not self.current_device:
            return
        
        # Show loading indicator
        loading_item = QTreeWidgetItem()
        loading_item.setText(0, tr("Loading..."))
        parent_item.addChild(loading_item)
        
        # Asynchronous load with worker
        thread = QThread()
        worker = FileListWorker()
        worker.moveToThread(thread)
        
        def on_loaded(files: list[RemoteFileInfo]) -> None:
            parent_item.removeChild(loading_item)
            
            folders = [f for f in files if f.is_dir]
            for folder in folders:
                item = QTreeWidgetItem()
                item.setText(0, f"📁 {folder.name}")
                item.setData(0, Qt.ItemDataRole.UserRole, folder.path)
                
                # Add placeholder
                placeholder = QTreeWidgetItem()
                placeholder.setText(0, "...")
                item.addChild(placeholder)
                
                parent_item.addChild(item)
        
        def on_error(error_msg: str) -> None:
            parent_item.removeChild(loading_item)
            
            # Show error popup + restore previous path if moved from path input
            if hasattr(self, "_previous_path") and self._previous_path:
                QMessageBox.warning(
                    self,
                    tr("Path error"),
                    tr("Path does not exist or is inaccessible:\n{0}").format(parent_path),
                )
                # Restore to previous path
                self.path_edit.setText(self._previous_path)
                self._previous_path = ""
            else:
                # Show error in tree if occurred during tree expansion
                error_item = QTreeWidgetItem()
                error_item.setText(0, f"⚠ {error_msg}")
                parent_item.addChild(error_item)
        
        def cleanup_thread():
            print("[DEBUG] folder_tree thread cleanup in progress...")
            thread.quit()
            thread.wait(1000)
            print("[DEBUG] folder_tree thread cleanup completed")
        
        worker.files_loaded.connect(on_loaded)
        worker.error_occurred.connect(on_error)
        worker.files_loaded.connect(cleanup_thread)
        worker.error_occurred.connect(cleanup_thread)
        
        device_serial = self.current_device.serial
        thread.started.connect(lambda: worker.list_files(device_serial, parent_path))
        thread.start()
    
    def _drag_enter_event(self, event) -> None:
        """Drag enter event handler.
        
        Args:
            event: QDragEnterEvent
        """
        print(f"[DEBUG] folder_tree._drag_enter_event: panel_type={self.panel_type}")
        print(f"[DEBUG] MIME formats: {event.mimeData().formats()}")
        
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
        print(f"[DEBUG] folder_tree._drag_move_event: panel_type={self.panel_type}")
        
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
        print(f"[DEBUG] folder_tree._drop_event: panel_type={self.panel_type}")
        
        if event.mimeData().hasFormat("application/x-adbcopy-files") or event.mimeData().hasText():
            print("[DEBUG] Drop allowed")
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            # Use folder path at drop location as destination
            # File info is managed in main_window
            self.files_dropped.emit([])
            print("[DEBUG] files_dropped signal emitted")
        else:
            print("[DEBUG] Drop rejected")
    
    def _add_to_history(self, path: str) -> None:
        """Add path to navigation history.
        
        Args:
            path: Path to add
        """
        # Don't add if it's the same as current
        if self._history_stack and self._history_index >= 0:
            if self._history_stack[self._history_index] == path:
                return
        
        # Remove forward history when navigating to new path
        if self._history_index < len(self._history_stack) - 1:
            self._history_stack = self._history_stack[:self._history_index + 1]
        
        # Add new path
        self._history_stack.append(path)
        self._history_index = len(self._history_stack) - 1
        
        # Update button states
        self._update_navigation_buttons()
    
    def _on_back_clicked(self) -> None:
        """Back button click handler."""
        if self._history_index > 0:
            self._history_index -= 1
            path = self._history_stack[self._history_index]
            self.path_edit.setText(path)
            self.folder_selected.emit(path)
            self._update_navigation_buttons()
    
    def _on_forward_clicked(self) -> None:
        """Forward button click handler."""
        if self._history_index < len(self._history_stack) - 1:
            self._history_index += 1
            path = self._history_stack[self._history_index]
            self.path_edit.setText(path)
            self.folder_selected.emit(path)
            self._update_navigation_buttons()
    
    def _update_navigation_buttons(self) -> None:
        """Update back/forward button states."""
        self.back_button.setEnabled(self._history_index > 0)
        self.forward_button.setEnabled(self._history_index < len(self._history_stack) - 1)
    
    def expand_and_select_path(self, path: str) -> None:
        """Expand tree to show and select the given path.
        
        Args:
            path: Path to expand and select
        """
        if self.panel_type == "local":
            self._expand_local_path(path)
        else:
            self._expand_remote_path(path)
    
    def _expand_local_path(self, path: str) -> None:
        """Expand local tree to show path.
        
        Args:
            path: Local path to expand to
        """
        from PyQt6.QtWidgets import QApplication
        import time
        
        print(f"[DEBUG] _expand_local_path called: {path}")
        
        # Update path input
        self.path_edit.setText(path)
        
        # Normalize path for comparison
        target_path = str(Path(path))
        
        # Recursively find and expand item
        def find_and_expand_local(parent_item: QTreeWidgetItem, target_path: str) -> QTreeWidgetItem | None:
            """Recursively find item and expand parents in local tree."""
            # Get stored path from UserRole
            item_path = parent_item.data(0, Qt.ItemDataRole.UserRole)
            
            # Skip virtual nodes (like "My PC") with no path
            if item_path is None:
                # Search in children for virtual nodes
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    result = find_and_expand_local(child, target_path)
                    if result:
                        return result
                return None
            
            # Normalize for comparison
            item_path_normalized = str(Path(item_path))
            
            print(f"[DEBUG] Checking local item: text='{parent_item.text(0)}', path='{item_path_normalized}'")
            
            # Exact match
            if item_path_normalized == target_path:
                print(f"[DEBUG] Found exact match!")
                return parent_item
            
            # Check if target is under this path
            try:
                # Use Path to check if target is relative to item_path
                target_path_obj = Path(target_path)
                item_path_obj = Path(item_path_normalized)
                
                # Check if target is under this item
                if target_path_obj == item_path_obj or item_path_obj in target_path_obj.parents:
                    print(f"[DEBUG] Target is under this item, expanding...")
                    
                    # Expand if collapsed
                    if not parent_item.isExpanded():
                        # Check for placeholder
                        if parent_item.childCount() == 1 and parent_item.child(0).text(0) == "...":
                            print(f"[DEBUG] Has placeholder, expanding to trigger load...")
                            self.tree_widget.expandItem(parent_item)
                            # Wait for lazy load
                            for _ in range(10):
                                QApplication.processEvents()
                                time.sleep(0.05)
                                if parent_item.childCount() > 1:
                                    break
                        else:
                            parent_item.setExpanded(True)
                    
                    # Search in children
                    for i in range(parent_item.childCount()):
                        child = parent_item.child(i)
                        if child.text(0) == "...":
                            continue
                        result = find_and_expand_local(child, target_path)
                        if result:
                            return result
                    
                    # If no child matched, this is as close as we can get
                    return parent_item
                    
            except Exception as e:
                print(f"[DEBUG] Error checking path relationship: {e}")
            
            return None
        
        # Start search from root (My PC)
        if self.tree_widget.topLevelItemCount() > 0:
            root_item = self.tree_widget.topLevelItem(0)
            result = find_and_expand_local(root_item, target_path)
            
            if result:
                # Expand final item if it has children
                if not result.isExpanded() and result.childCount() > 0:
                    if result.childCount() == 1 and result.child(0).text(0) == "...":
                        self.tree_widget.expandItem(result)
                        # Wait a bit for load
                        for _ in range(5):
                            QApplication.processEvents()
                            time.sleep(0.05)
                            if result.childCount() > 1:
                                break
                    else:
                        result.setExpanded(True)
                
                # Select and scroll to item
                self.tree_widget.setCurrentItem(result)
                self.tree_widget.scrollToItem(result)
                print(f"[DEBUG] Selected and scrolled to: {result.text(0)}")
            else:
                print(f"[DEBUG] Path not found in tree: {path}")
    
    def _expand_remote_path(self, path: str) -> None:
        """Expand remote tree to show path.
        
        Args:
            path: Remote path to expand to
        """
        if not self.current_device or not path:
            return
        
        print(f"[DEBUG] _expand_remote_path called: {path}")
        
        # Recursively find and expand item
        def find_and_expand(parent_item: QTreeWidgetItem, target_path: str) -> QTreeWidgetItem | None:
            """Recursively find item and expand parents."""
            # Check if this item matches
            item_path = parent_item.data(0, Qt.ItemDataRole.UserRole)
            
            # Skip items without path (like "Loading...")
            if item_path is None:
                return None
            
            print(f"[DEBUG] Checking item: text='{parent_item.text(0)}', path='{item_path}', target='{target_path}'")
            
            if item_path == target_path:
                print(f"[DEBUG] Found exact match!")
                return parent_item
            
            # Expand this item if target path is under it
            if target_path.startswith(item_path.rstrip('/') + '/'):
                print(f"[DEBUG] Target is under this item, expanding...")
                
                # Expand if collapsed
                if not parent_item.isExpanded():
                    # Check for placeholder
                    if parent_item.childCount() == 1 and parent_item.child(0).text(0) == "...":
                        print(f"[DEBUG] Has placeholder, expanding to trigger load...")
                        self.tree_widget.expandItem(parent_item)
                        # Wait for lazy load (async operation needs time)
                        from PyQt6.QtWidgets import QApplication
                        import time
                        for _ in range(10):  # Wait up to 1 second
                            QApplication.processEvents()
                            time.sleep(0.1)
                            # Check if loading is done
                            if parent_item.childCount() > 1 or (parent_item.childCount() == 1 and parent_item.child(0).text(0) != "Loading..."):
                                break
                        print(f"[DEBUG] After expansion, child count: {parent_item.childCount()}")
                    else:
                        parent_item.setExpanded(True)
                
                # Search in children (skip "Loading..." items)
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    # Skip loading/placeholder items
                    if child.text(0) in ("...", "Loading..."):
                        continue
                    result = find_and_expand(child, target_path)
                    if result:
                        return result
            
            return None
        
        # Start search from root
        if self.tree_widget.topLevelItemCount() > 0:
            root_item = self.tree_widget.topLevelItem(0)
            result = find_and_expand(root_item, path)
            
            if result:
                # Expand final item if it has children
                if not result.isExpanded() and result.childCount() > 0:
                    if result.childCount() == 1 and result.child(0).text(0) == "...":
                        self.tree_widget.expandItem(result)
                    else:
                        result.setExpanded(True)
                
                # Select and scroll
                self.tree_widget.setCurrentItem(result)
                self.tree_widget.scrollToItem(result)
                print(f"[DEBUG] Selected and scrolled to: {result.text(0)}")
            else:
                print(f"[DEBUG] Path not found in tree: {path}")
                self.path_edit.setText(path)
        else:
            print(f"[DEBUG] No top-level items in tree")
            self.path_edit.setText(path)

