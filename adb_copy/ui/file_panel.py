"""File panel widget module.

Panel that vertically combines folder tree and file detail view.
"""

from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from adb_copy.core.adb_manager import AdbDevice
from adb_copy.ui.folder_tree_widget import FolderTreeWidget
from adb_copy.ui.file_detail_widget import FileDetailWidget, MY_PC_VIRTUAL_PATH
from adb_copy.i18n import tr


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
        
        # --- History navigation: keyboard + mouse XButton ---
        # Keyboard: Alt+Left / Alt+Right (standard) + Backspace / media Back/Forward keys.
        # WidgetWithChildrenShortcut so only the focused panel reacts.
        for keys, handler in (
            (QKeySequence("Alt+Left"), self.folder_tree._on_back_clicked),
            (QKeySequence(Qt.Key.Key_Backspace), self.folder_tree._on_back_clicked),
            (QKeySequence(Qt.Key.Key_Back), self.folder_tree._on_back_clicked),
            (QKeySequence("Alt+Right"), self.folder_tree._on_forward_clicked),
            (QKeySequence(Qt.Key.Key_Forward), self.folder_tree._on_forward_clicked),
        ):
            sc = QShortcut(keys, self)
            sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            sc.activated.connect(handler)
        
        # Mouse: XButton1 / XButton2 anywhere inside the panel. QTableWidget
        # and QTreeWidget consume their own mousePressEvent so we install
        # an event filter on both the widgets and their viewports plus the
        # path edit, covering every clickable region in the panel.
        for w in (
            self.file_detail.table,
            self.file_detail.table.viewport(),
            self.folder_tree.tree_widget,
            self.folder_tree.tree_widget.viewport(),
            self.folder_tree.path_edit,
        ):
            w.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Route mouse Back/Forward buttons to this panel's history."""
        if event.type() == QEvent.Type.MouseButtonPress:
            btn = event.button()
            if btn == Qt.MouseButton.BackButton:
                self.folder_tree._on_back_clicked()
                return True
            if btn == Qt.MouseButton.ForwardButton:
                self.folder_tree._on_forward_clicked()
                return True
        return super().eventFilter(obj, event)
    
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
        # Also update path input in folder tree (use friendly label for virtual path)
        if folder_path == MY_PC_VIRTUAL_PATH:
            self.folder_tree.path_edit.setText(tr("My PC"))
        else:
            self.folder_tree.path_edit.setText(folder_path)
        self.file_detail.load_path(folder_path)
        self.path_changed.emit(folder_path)
    
    def _on_folder_double_clicked(self, folder_path: str) -> None:
        """Called when folder is double-clicked in file detail.
        
        Args:
            folder_path: Double-clicked folder path
        """
        # Add to navigation history
        self.folder_tree._add_to_history(folder_path)
        
        # Expand and select in tree (skip for virtual paths)
        if folder_path != MY_PC_VIRTUAL_PATH:
            self.folder_tree.expand_and_select_path(folder_path)
        else:
            self.folder_tree.path_edit.setText(tr("My PC"))
        
        # Update file detail
        self.file_detail.load_path(folder_path)
        self.path_changed.emit(folder_path)

    def _on_refresh_requested(self) -> None:
        """Refresh request handler.
        
        Reloads file list AND syncs the matching tree branch so that
        new/deleted/renamed folders show up immediately in the tree.
        """
        if self.file_detail.current_path:
            self.file_detail.load_path(self.file_detail.current_path)
            self.folder_tree.refresh_branch_at(self.file_detail.current_path)