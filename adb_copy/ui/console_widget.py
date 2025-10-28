"""Console message widget module.

Console area that displays INFO/DEBUG log messages.
"""

from datetime import datetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QTextCursor

from adb_copy.i18n import tr


class ConsoleWidget(QWidget):
    """Console message widget class.
    
    Displays log messages in chronological order.
    """
    
    def __init__(self) -> None:
        """Initialize ConsoleWidget instance."""
        super().__init__()
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Text edit (read-only)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        # No max height limit (controlled by Splitter)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #3e3e3e;
            }
        """)
        
        layout.addWidget(self.text_edit)
        
        self.log_info(tr("ADBCopy started"))
    
    def log_info(self, message: str) -> None:
        """Log INFO level message.
        
        Args:
            message: Log message
        """
        self._append_log("INFO", message, "#4ec9b0")
    
    def log_debug(self, message: str) -> None:
        """Log DEBUG level message.
        
        Args:
            message: Log message
        """
        self._append_log("DEBUG", message, "#808080")
    
    def log_error(self, message: str) -> None:
        """Log ERROR level message.
        
        Args:
            message: Log message
        """
        self._append_log("ERROR", message, "#f48771")
    
    def log_warning(self, message: str) -> None:
        """Log WARNING level message.
        
        Args:
            message: Log message
        """
        self._append_log("WARN", message, "#dcdcaa")
    
    def _append_log(self, level: str, message: str, color: str) -> None:
        """Append log message.
        
        Args:
            level: Log level (INFO, DEBUG, ERROR, WARN)
            message: Log message
            color: HTML color code
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<span style="color: #808080;">[{timestamp}]</span> '
            f'<span style="color: {color};">[{level}]</span> '
            f'<span style="color: #d4d4d4;">{message}</span>'
        )
        
        self.text_edit.append(html)
        
        # Always scroll to latest message
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_edit.setTextCursor(cursor)
    
    def clear(self) -> None:
        """Clear console content."""
        self.text_edit.clear()

