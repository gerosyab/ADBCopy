"""ADBCopy application entry point.

This module initializes PyQt6 QApplication and starts the main window.
"""

import sys
import platform
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from adb_copy.main_window import MainWindow


def main() -> int:
    """Start the application.
    
    Returns:
        int: Application exit code.
    """
    # Fix Windows taskbar icon
    if platform.system() == "Windows":
        import ctypes
        # Set AppUserModelID to make Windows show the correct icon in taskbar
        myappid = "gerosyab.adbcopy.fileexplorer.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    app.setApplicationName("ADBCopy")
    app.setOrganizationName("ADBCopy")
    
    # Set application icon
    icon_path = Path(__file__).parent / "resources" / "icons" / "favicon.ico"
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

