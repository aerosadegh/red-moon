import os
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QStatusBar,
    QDialog,
    QTextEdit,
    QPushButton,
    QFileDialog,
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QIcon
from redis_logic import RedisSubscriber


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class OutputWindow(QDialog):
    def __init__(self, channel_name, parent=None):
        super().__init__(parent)
        self.channel_name = channel_name
        self.setWindowTitle(f"Output for {channel_name}")
        layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_content)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def update_output(self, data: str):
        self.output_text.append("\n" + data)

    def export_content(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            f"{self.channel_name}.txt",
            "Text Files (*.txt);;All Files (*)",
            options=options,
        )
        if file_name:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(self.output_text.toPlainText())


class RedisMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.subscriber = None
        self.output_windows = {}  # Initialize the output_windows dictionary

    def initUI(self):
        self.setWindowTitle("Redis Monitoring Tool")
        layout = QVBoxLayout()
        self.setWindowIcon(QIcon(resource_path("assets/red-moon.png")))

        self.redis_url_label = QLabel("Redis URL:")
        self.redis_url_input = QLineEdit()
        layout.addWidget(self.redis_url_label)
        layout.addWidget(self.redis_url_input)

        self.channel_pattern_label = QLabel("Channel Pattern:")
        self.channel_pattern_input = QLineEdit()

        self.redis_url_input.setPlaceholderText("redis://localhost:6379")
        self.redis_url_input.setText("redis://localhost:6379")
        self.channel_pattern_input.setPlaceholderText("*")
        self.channel_pattern_input.setText("*")

        layout.addWidget(self.channel_pattern_label)
        layout.addWidget(self.channel_pattern_input)

        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        layout.addWidget(self.stop_button)

        self.channel_list = QListWidget()
        self.channel_list.itemClicked.connect(self.open_output_window)
        layout.addWidget(self.channel_list)

        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        self.status_bar.showMessage("Status: Not Monitoring")

        self.setLayout(layout)

    def start_monitoring(self):
        redis_url = self.redis_url_input.text()
        channel_pattern = self.channel_pattern_input.text()
        self.subscriber = RedisSubscriber(redis_url, channel_pattern)
        self.subscriber.new_channel.connect(self.add_channel)
        self.subscriber.start()
        self.status_bar.showMessage("Status: Monitoring")

    def stop_monitoring(self):
        if hasattr(self, "subscriber") and self.subscriber:
            self.subscriber.terminate()
            self.status_bar.showMessage("Status: Not Monitoring")

    def add_channel(self, channel_name, data):
        # Check if the channel already exists in the list
        items = [self.channel_list.item(i).text() for i in range(self.channel_list.count())]
        if channel_name in items:
            # Remove the existing item
            index = items.index(channel_name)
            self.channel_list.takeItem(index)
        # Create a new QListWidgetItem
        new_item = QListWidgetItem(channel_name)
        # Add the new item to the top of the list
        self.channel_list.insertItem(0, new_item)
        self.highlight_item(new_item)

        # Ensure the output window exists
        if channel_name not in self.output_windows:
            self.output_windows[channel_name] = OutputWindow(channel_name)
        # Update the output window with the new data
        self.output_windows[channel_name].update_output(data)

    def highlight_item(self, item):
        # Set the background color to highlight
        item.setBackground(QColor("yellow"))
        # Create a QTimer to revert the background color after 1 second
        QTimer.singleShot(1000, lambda: item.setBackground(QColor("white")))

    def open_output_window(self, item):
        channel_name = item.text()
        self.output_windows[channel_name] = OutputWindow(channel_name)
        self.output_windows[channel_name].show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = RedisMonitor()
    monitor.show()
    sys.exit(app.exec_())
