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
    QAction,
    QMenuBar,
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtGui import QColor

from gui.utils import resource_path
from gui.output_window import OutputWindow
from redis_logic import RedisSubscriber


class RedisMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.subscriber = None
        self.output_windows = {}  # Initialize the output_windows dictionary
        self.open_window_positions = []
        self.reorder_channels = True

    def initUI(self):
        self.setWindowTitle("Redis Monitoring Tool")
        layout = QVBoxLayout()
        self.setWindowIcon(QIcon(resource_path("assets/red-moon.png")))

        self.menu_bar = QMenuBar(self)
        self.menu = self.menu_bar.addMenu("Settings")
        self.reorder_action = QAction("Reorder Channels", self)
        self.reorder_action.setCheckable(True)
        self.reorder_action.setChecked(True)
        self.reorder_action.triggered.connect(self.toggle_reorder)
        self.menu.addAction(self.reorder_action)
        layout.setMenuBar(self.menu_bar)

        self.redis_url_label = QLabel("Redis URL:")
        self.redis_url_input = QLineEdit()
        layout.addWidget(self.redis_url_label)
        layout.addWidget(self.redis_url_input)

        self.channel_pattern_label = QLabel("Channel Pattern:")
        self.channel_pattern_input = QLineEdit()

        self.redis_url_input.setPlaceholderText("redis://localhost:6379")
        self.redis_url_input.setText("redis://192.168.1.102:6379")
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
        self.setMaximumSize(self.width() + 200, self.height() + 100)

    def closeEvent(self, event):
        for window in self.output_windows.values():
            window.close()
        event.accept()

    def toggle_reorder(self):
        self.reorder_channels = self.reorder_action.isChecked()

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
        # Get the list of channel names
        channels_names = [
            self.channel_list.item(i).text() for i in range(self.channel_list.count())
        ]

        # Check if the channel already exists in the list
        if channel_name in channels_names:
            index = channels_names.index(channel_name)
            item = (
                self.channel_list.takeItem(index)
                if self.reorder_channels
                else self.channel_list.item(index)
            )
        else:
            item = QListWidgetItem(channel_name)
            self.channel_list.addItem(item)

        # Highlight the item
        self.highlight_item(item)

        # Reorder the item if necessary
        if self.reorder_channels and channel_name in channels_names:
            self.channel_list.insertItem(0, item)

        # Ensure the output window exists
        if channel_name not in self.output_windows:
            self.output_windows[channel_name] = OutputWindow(channel_name)

        # Update the output window with the new data
        self.output_windows[channel_name].update_output(data)

    def highlight_item(self, item):
        # Define the start and end colors
        start_color = QColor("yellow")
        end_color = QColor("white")

        # Set the initial background color
        item.setBackground(start_color)

        # Define the duration and interval for the transition
        duration = 1000  # Duration in milliseconds
        interval = 50  # Interval in milliseconds

        # Calculate the number of steps
        steps = duration // interval

        # Calculate the color change per step
        delta_r = (end_color.red() - start_color.red()) / steps
        delta_g = (end_color.green() - start_color.green()) / steps
        delta_b = (end_color.blue() - start_color.blue()) / steps

        # Initialize the current step
        current_step = 0

        def update_color():
            nonlocal current_step
            if current_step < steps:
                # Calculate the new color
                new_color = QColor(
                    int(start_color.red() + delta_r * current_step),
                    int(start_color.green() + delta_g * current_step),
                    int(start_color.blue() + delta_b * current_step),
                )
                # Set the new background color
                item.setBackground(new_color)
                # Increment the current step
                current_step += 1
            else:
                # Stop the timer when the transition is complete
                timer.stop()

        # Create a QTimer to update the color at regular intervals
        timer = QTimer()
        timer.timeout.connect(update_color)
        timer.start(interval)

    def open_output_window(self, item: QListWidgetItem):
        channel_name = item.text()
        if channel_name not in self.output_windows:
            return  # Ensure the window exists

        output_window = self.output_windows[channel_name]
        if not isinstance(output_window, OutputWindow):
            raise TypeError("output_window must be an OutputWindow")

        output_window.show()

        # Constants for positioning
        INITIAL_OFFSET_Y = 200
        WINDOW_SPACING_Y = 275
        MINIMUM_WIDTH = 500
        SCREEN_MARGIN = 50

        if not hasattr(self, "open_window_positions"):
            self.open_window_positions = []

        # Find the next available position
        if self.open_window_positions:
            self.output_window_x, self.output_window_y = self.open_window_positions.pop(0)
        else:
            if not hasattr(self, "output_window_x"):
                self.output_window_x = self.x() + self.width()
                self.output_window_y = self.y() - INITIAL_OFFSET_Y
            else:
                self.output_window_y += WINDOW_SPACING_Y

            screen_geometry = QApplication.desktop().availableGeometry()

            if (
                self.output_window_x + output_window.width()
                > screen_geometry.width() - SCREEN_MARGIN
            ):
                self.output_window_x = self.x() + self.width()  # Reset to right of main window

            if (
                self.output_window_y + output_window.height()
                > screen_geometry.height() - SCREEN_MARGIN
            ):
                self.output_window_y = self.y()  # Reset to top of screen

        output_window.move(self.output_window_x, self.output_window_y)
        output_window.resize(MINIMUM_WIDTH, output_window.height())
        output_window.setMinimumWidth(MINIMUM_WIDTH)

        # Store the position when the window is closed
        output_window.destroyed.connect(
            lambda: self.open_window_positions.append((self.output_window_x, self.output_window_y))
        )
