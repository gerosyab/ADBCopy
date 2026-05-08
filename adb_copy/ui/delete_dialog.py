"""Delete confirmation dialog with Trash / Permanent choice."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from adb_copy.i18n import tr


class DeleteDialog(QDialog):
    """Two-mode delete dialog.
    
    Local panel: user chooses between moving to trash or permanent delete.
    Remote panel (`allow_trash=False`): only permanent confirm is shown
    since Android `rm -rf` is always permanent.
    """
    
    CANCEL = 0
    TRASH = 1
    PERMANENT = 2
    
    def __init__(
        self,
        item_count: int,
        allow_trash: bool = True,
        sample_name: str = "",
        parent=None,
    ) -> None:
        """Initialize DeleteDialog.
        
        Args:
            item_count: Number of items being deleted.
            allow_trash: Whether the trash option should be available.
            sample_name: Optional sample item name to show in the message.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.allow_trash = allow_trash
        self.item_count = item_count
        self.sample_name = sample_name
        self._result = self.CANCEL
        
        self.setWindowTitle(tr("Confirm Delete"))
        self.setModal(True)
        self.setMinimumWidth(420)
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header message
        if self.sample_name and self.item_count == 1:
            header_text = tr("Delete this item?") + f"\n\n{self.sample_name}"
        else:
            header_text = tr("Delete {0} item(s)?").format(self.item_count)
        header = QLabel(header_text)
        header.setWordWrap(True)
        header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(header)
        
        # Choice radios
        self.button_group = QButtonGroup(self)
        
        if self.allow_trash:
            self.trash_radio = QRadioButton(tr("Move to Trash"))
            self.trash_radio.setChecked(True)
            self.button_group.addButton(self.trash_radio, self.TRASH)
            layout.addWidget(self.trash_radio)
        
        self.permanent_radio = QRadioButton(tr("Permanent Delete"))
        if not self.allow_trash:
            self.permanent_radio.setChecked(True)
        self.button_group.addButton(self.permanent_radio, self.PERMANENT)
        layout.addWidget(self.permanent_radio)
        
        # Permanent warning (red, italic)
        self.warning_label = QLabel(tr("This action cannot be undone."))
        self.warning_label.setStyleSheet(
            "color: #b00020; font-weight: bold; padding-left: 22px;"
        )
        self.warning_label.setVisible(not self.allow_trash)
        layout.addWidget(self.warning_label)
        
        if self.allow_trash:
            self.trash_radio.toggled.connect(self._update_warning)
            self.permanent_radio.toggled.connect(self._update_warning)
        
        layout.addSpacing(8)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        ok_btn = QPushButton(tr("OK"))
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_ok)
        buttons_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _update_warning(self) -> None:
        self.warning_label.setVisible(self.permanent_radio.isChecked())
    
    def _on_ok(self) -> None:
        if self.allow_trash and self.trash_radio.isChecked():
            self._result = self.TRASH
        else:
            self._result = self.PERMANENT
        self.accept()
    
    def get_choice(self) -> int:
        """Return the user's choice (CANCEL/TRASH/PERMANENT)."""
        if self.result() == QDialog.DialogCode.Rejected:
            return self.CANCEL
        return self._result
