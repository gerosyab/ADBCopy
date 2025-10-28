"""File overwrite dialog module.

Dialog for selecting overwrite options when file already exists.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from adb_copy.i18n import tr


class OverwriteDialog(QDialog):
    """File overwrite dialog class.
    
    Provides FileZilla-style overwrite options.
    """
    
    # Return value constants
    OVERWRITE = 1
    SKIP = 2
    RENAME = 3
    CANCEL = 4
    
    def __init__(
        self,
        filename: str,
        source_size: int = 0,
        dest_size: int = 0,
        parent=None,
    ) -> None:
        """Initialize OverwriteDialog instance.
        
        Args:
            filename: Filename
            source_size: Source file size
            dest_size: Destination file size
            parent: Parent widget
        """
        super().__init__(parent)
        self.filename = filename
        self.source_size = source_size
        self.dest_size = dest_size
        self.apply_to_all = False
        
        self.setWindowTitle(tr("File already exists"))
        self.setModal(True)
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Message
        message = QLabel(f"{tr('File already exists')}:\n\n{self.filename}")
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # File information
        info_layout = QVBoxLayout()
        
        source_label = QLabel(f"Source size: {self._format_size(self.source_size)}")
        info_layout.addWidget(source_label)
        
        dest_label = QLabel(f"Destination size: {self._format_size(self.dest_size)}")
        info_layout.addWidget(dest_label)
        
        layout.addLayout(info_layout)
        layout.addSpacing(10)
        
        # Apply to all checkbox
        self.apply_all_checkbox = QCheckBox(tr("Apply to all"))
        layout.addWidget(self.apply_all_checkbox)
        
        layout.addSpacing(10)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        overwrite_btn = QPushButton(tr("Overwrite"))
        overwrite_btn.clicked.connect(lambda: self._done(self.OVERWRITE))
        buttons_layout.addWidget(overwrite_btn)
        
        skip_btn = QPushButton(tr("Skip"))
        skip_btn.clicked.connect(lambda: self._done(self.SKIP))
        buttons_layout.addWidget(skip_btn)
        
        rename_btn = QPushButton(tr("Rename"))
        rename_btn.clicked.connect(lambda: self._done(self.RENAME))
        buttons_layout.addWidget(rename_btn)
        
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.clicked.connect(lambda: self._done(self.CANCEL))
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _done(self, result: int) -> None:
        """Close dialog.
        
        Args:
            result: Selection result
        """
        self.apply_to_all = self.apply_all_checkbox.isChecked()
        self.done(result)
    
    def _format_size(self, size: int) -> str:
        """Format file size.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size == 0:
            return "Unknown"
        
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        
        return f"{size:.1f} PB"

