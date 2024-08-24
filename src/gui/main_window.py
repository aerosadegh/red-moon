from __future__ import annotations
import time

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStatusBar,
    QPushButton,
    QAction,
    QMenuBar,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from plyer import notification

from redis_logic import RedisSubscriber

from .utils import START_STYLESHEET, STOP_STYLESHEET, resource_path
from .output_window import OutputWindowUI
from .output_manager import OutputWindowManager
from .highlighting import Highlighter


class UISetup:
    def __init__(self, main_widget: "RedisMonitor"):
        self.main_widget = main_widget

        self.menu_bar = None
        self.redis_url_input = None
        self.channel_pattern_input = None
        self.timeout_value = 0  # Initialize the timeout value

        self.channel_update_timer = QTimer()
        self.channel_update_timer.timeout.connect(self.check_channel_updates)
        self.channel_update_timer.start(60000)  # Start the timer with a 1-minute interval

        self.start_stop_button: QPushButton

    def check_channel_updates(self):
        self.main_widget.channel_manager.check_channel_updates()

    def setup_ui(self):
        self.main_widget.setWindowTitle("Redis Monitoring Tool")
        self.main_widget.setMinimumWidth(400)
        layout = QVBoxLayout()
        self.main_widget.setWindowIcon(QIcon(resource_path("assets/red-moon.png")))

        self.menu_bar = self.create_menu_bar()
        layout.setMenuBar(self.menu_bar)

        self.redis_url_input = self.create_labeled_input(
            layout,
            "Redis URL:",
            "redis://localhost:6379",
            "redis://localhost:6379",
        )
        self.channel_pattern_input = self.create_labeled_input(
            layout,
            "Channel Pattern:",
            "*",
            "*",
        )

        self.add_monitoring_buttons(layout)

        self.main_widget.channel_list = QListWidget()
        self.main_widget.channel_list.itemClicked.connect(self.main_widget.open_output_window)
        layout.addWidget(self.main_widget.channel_list)

        self.main_widget.status_bar = QStatusBar()
        layout.addWidget(self.main_widget.status_bar)
        self.main_widget.status_bar.showMessage("Status: Not Monitoring")

        self.main_widget.setLayout(layout)
        self.main_widget.setMaximumSize(
            self.main_widget.width() + 200, self.main_widget.height() + 100
        )

    def add_monitoring_buttons(self, layout: QVBoxLayout):
        button_layout = QHBoxLayout()  # Horizontal layout for the buttons

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.clicked.connect(self.main_widget.toggle_monitoring)
        # Set the button to be circular
        size = 50  # Set the desired size for the button
        self.start_stop_button.setFixedSize(size, size)
        self.start_stop_button.setStyleSheet(START_STYLESHEET)
        button_layout.addWidget(self.start_stop_button)
        layout.addLayout(button_layout)

    def create_menu_bar(self):
        menu_bar = QMenuBar(self.main_widget)
        menu = menu_bar.addMenu("Settings")
        reorder_action = QAction("Reorder Channels", self.main_widget)
        reorder_action.setCheckable(True)
        reorder_action.setChecked(True)
        reorder_action.triggered.connect(self.main_widget.toggle_reorder)
        menu.addAction(reorder_action)
        return menu_bar

    def create_labeled_input(
        self, layout: QVBoxLayout, label_text: str, placeholder_text: str, default_text: str
    ):
        label = QLabel(label_text)
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder_text)
        input_field.setText(default_text)
        layout.addWidget(label)
        layout.addWidget(input_field)
        return input_field

    def create_button(self, layout, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button


class ChannelManager:
    def __init__(self, main_widget: "RedisMonitor"):
        self.main_widget = main_widget
        self.channel_last_update: dict[str, float] = {}

    def add_channel(self, channel_name: str, data: str, status: str):
        channels_names = [
            self.main_widget.channel_list.item(i).text()
            for i in range(self.main_widget.channel_list.count())
        ]
        self.channel_last_update[channel_name] = time.time()
        if status != "success":
            self.main_widget.status_bar.showMessage(f"Status: {status}")
            return
        self.main_widget.status_bar.showMessage("Status: Monitoring")

        if channel_name in channels_names:
            index = channels_names.index(channel_name)
            item = (
                self.main_widget.channel_list.takeItem(index)
                if self.main_widget.reorder_channels
                else self.main_widget.channel_list.item(index)
            )
        else:
            item = QListWidgetItem(channel_name)
            self.main_widget.channel_list.addItem(item)

        Highlighter.highlight_item(item)

        if self.main_widget.reorder_channels and channel_name in channels_names:
            self.main_widget.channel_list.insertItem(0, item)

        if channel_name not in self.main_widget.output_windows_ui:
            self.main_widget.output_windows_ui[channel_name] = OutputWindowUI(channel_name)

        self.main_widget.output_windows_ui[channel_name].update_output(data)

    def check_channel_updates(self):
        current_time = time.time()
        for channel_name, last_update_time in self.channel_last_update.items():
            if (
                current_time - last_update_time > 60
            ):  # Check if 1 minute has passed since last update
                notification.notify(
                    "No Data Received",
                    f"No data received for channel '{channel_name}' in the last minute.",
                )


class RedisMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.init_classes()
        self.ui_setup.setup_ui()

        self.reorder_channels = True
        self.subscriber = None
        self.monitoring = False  # To track the state of monitoring

    def init_classes(self):
        self.ui_setup = UISetup(self)
        self.channel_manager = ChannelManager(self)
        self.window_manager = OutputWindowManager(self)
        self.output_windows_ui = {}
        self.open_window_positions = []

    def toggle_reorder(self):
        self.reorder_channels = not self.reorder_channels

    def toggle_monitoring(self):
        if self.monitoring:
            self.stop_monitoring()
            self.ui_setup.start_stop_button.setStyleSheet(START_STYLESHEET)
            self.ui_setup.start_stop_button.setText("Start")
        else:
            self.start_monitoring()
            self.ui_setup.start_stop_button.setStyleSheet(STOP_STYLESHEET)
            self.ui_setup.start_stop_button.setText("Stop")
        self.monitoring = not self.monitoring

    def start_monitoring(self):
        redis_url = self.ui_setup.redis_url_input.text()
        channel_pattern = self.ui_setup.channel_pattern_input.text()
        self.subscriber = RedisSubscriber(redis_url, channel_pattern)
        self.subscriber.new_channel.connect(self.channel_manager.add_channel)
        self.subscriber.start()
        self.status_bar.showMessage("Status: Monitoring")

    def stop_monitoring(self):
        self.channel_manager.channel_last_update.clear()
        if self.subscriber:
            self.subscriber.terminate()
            self.status_bar.showMessage("Status: Not Monitoring")

    def open_output_window(self, item: QListWidgetItem):
        self.window_manager.open_output_window(item)

    def closeEvent(self, event):
        for window in self.output_windows_ui.values():
            window.close()
        event.accept()
