"""File panel widget module.

Panel that vertically combines folder tree and file detail view.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from adb_copy.core.adb_manager import AdbDevice
from adb_copy.ui.folder_tree_widget import FolderTreeWidget
from adb_copy.ui.file_detail_widget import FileDetailWidget


class FilePanel(QWidget):
    """File panel widget class.
    
    Combines folder tree (top) and file detail view (bottom).
    
    Signals:
        path_changed: Emitted when path changes (str)
    """
    
    path_changed = pyqtSignal(str)
    
    def __init__(self, panel_type: str = "local") -> None:
        """Initialize FilePanel instance.
        
        Args:
            panel_type: Panel type. "local" or "remote"
        """
        super().__init__()
        self.panel_type = panel_type
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Vertical splitter (folder tree + file detail)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Folder tree (top)
        self.folder_tree = FolderTreeWidget(panel_type=self.panel_type)
        self.folder_tree.folder_selected.connect(self._on_folder_selected)
        splitter.addWidget(self.folder_tree)
        
        # File detail (bottom)
        self.file_detail = FileDetailWidget(panel_type=self.panel_type)
        self.file_detail.folder_double_clicked.connect(self._on_folder_double_clicked)
        self.file_detail.refresh_requested.connect(self._on_refresh_requested)
        splitter.addWidget(self.file_detail)
        
        # Set ratio (1:2 = folder_tree:file_detail)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
    
    def set_device(self, device: AdbDevice | None) -> None:
        """Set connected device for remote panel.
        
        Args:
            device: Connected ADB device
        """
        if self.panel_type != "remote":
            return
        
        self.folder_tree.set_device(device)
        self.file_detail.set_device(device)
    
    def _on_folder_selected(self, folder_path: str) -> None:
        """Called when folder is selected in folder tree.
        
        Args:
            folder_path: Selected folder path
        """
        # Also update path input in folder tree
        self.folder_tree.path_edit.setText(folder_path)
        self.file_detail.load_path(folder_path)
        self.path_changed.emit(folder_path)
    
    def _on_folder_double_clicked(self, folder_path: str) -> None:
        """Called when folder is double-clicked in file detail.
        
        Args:
            folder_path: Double-clicked folder path
        """
        # Update folder tree (if implementation needed)
        self.file_detail.load_path(folder_path)
        self.path_changed.emit(folder_path)

    def _on_refresh_requested(self) -> None:
        """Refresh request handler."""
        if self.file_detail.current_path:
            self.file_detail.load_path(self.file_detail.current_path)