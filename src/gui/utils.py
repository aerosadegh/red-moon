import sys
import os


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")

    return os.path.join(base_path, relative_path)


START_STYLESHEET = """
                QPushButton {
                    border-radius: 25;
                    background-color: #28a745;
                    color: white;
                    font-size: 12px;
                }
                QPushButton:pressed {
                    background-color: #218838;
                }
                QPushButton:hover {
                    background-color: #34ce57;
                }
            """


STOP_STYLESHEET = """
                QPushButton {
                    border-radius: 25;
                    background-color: #dc3545;
                    color: white;
                    font-size: 12px;
                }
                QPushButton:pressed {
                    background-color: #c82333;
                }
                QPushButton:hover {
                    background-color: #e4606d;
                }
            """
