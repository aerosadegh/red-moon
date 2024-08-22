from __future__ import annotations

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QStatusBar,
    QPushButton,
    QAction,
    QMenuBar,
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtGui import QColor

from gui.utils import resource_path
from gui.output_window import OutputWindow
from redis_logic import RedisSubscriber


class UISetup:
    def __init__(self, main_widget: "RedisMonitor"):
        self.main_widget = main_widget

        self.menu_bar = None
        self.redis_url_label = None
        self.redis_url_input = None
        self.channel_pattern_label = None
        self.channel_pattern_input = None
        self.start_button = None
        self.stop_button = None

    def setup_ui(self):
        self.main_widget.setWindowTitle("Redis Monitoring Tool")
        self.main_widget.setMinimumWidth(500)
        layout = QVBoxLayout()
        self.main_widget.setWindowIcon(QIcon(resource_path("assets/red-moon.png")))

        self.menu_bar = self.create_menu_bar()
        layout.setMenuBar(self.menu_bar)

        self.redis_url_label, self.redis_url_input = self.create_labeled_input(
            layout, "Redis URL:", "redis://localhost:6379", "redis://localhost:6379"
        )
        self.channel_pattern_label, self.channel_pattern_input = self.create_labeled_input(
            layout, "Channel Pattern:", "*", "*"
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

        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.main_widget.start_monitoring)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.main_widget.stop_monitoring)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)  # Add the horizontal layout to the main layout

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
        return label, input_field

    def create_button(self, layout, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button


class ChannelManager:
    def __init__(self, main_widget: "RedisMonitor"):
        self.main_widget = main_widget

    def add_channel(self, channel_name: str, data: str):
        channels_names = [
            self.main_widget.channel_list.item(i).text()
            for i in range(self.main_widget.channel_list.count())
        ]

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

        if channel_name not in self.main_widget.output_windows:
            self.main_widget.output_windows[channel_name] = OutputWindow(channel_name)

        self.main_widget.output_windows[channel_name].update_output(data)


class Highlighter:
    @staticmethod
    def highlight_item(item: QListWidgetItem):
        start_color = QColor("yellow")
        end_color = QColor("white")

        item.setBackground(start_color)

        duration = 1000
        interval = 50

        steps = duration // interval
        delta_r = (end_color.red() - start_color.red()) / steps
        delta_g = (end_color.green() - start_color.green()) / steps
        delta_b = (end_color.blue() - start_color.blue()) / steps

        current_step = 0

        def update_color():
            nonlocal current_step
            if current_step < steps:
                new_color = QColor(
                    int(start_color.red() + delta_r * current_step),
                    int(start_color.green() + delta_g * current_step),
                    int(start_color.blue() + delta_b * current_step),
                )
                item.setBackground(new_color)
                current_step += 1
            else:
                timer.stop()

        timer = QTimer()
        timer.timeout.connect(update_color)
        timer.start(interval)


class OutputWindowManager:
    def __init__(self, main_widget: "RedisMonitor"):
        self.main_widget = main_widget

    def open_output_window(self, item: QListWidgetItem):
        channel_name = item.text()
        if channel_name not in self.main_widget.output_windows:
            return

        output_window = self.main_widget.output_windows[channel_name]
        output_window.show()

        INITIAL_OFFSET_Y = 200
        WINDOW_SPACING_Y = 275
        MINIMUM_WIDTH = 500
        SCREEN_MARGIN = 50

        if not self.main_widget.open_window_positions:
            if not hasattr(self.main_widget, "output_window_x"):
                self.main_widget.output_window_x = self.main_widget.x() + self.main_widget.width()
                self.main_widget.output_window_y = self.main_widget.y() - INITIAL_OFFSET_Y
            else:
                self.main_widget.output_window_y += WINDOW_SPACING_Y

            screen_geometry = QApplication.desktop().availableGeometry()

            if (
                self.main_widget.output_window_x + output_window.width()
                > screen_geometry.width() - SCREEN_MARGIN
            ):
                self.main_widget.output_window_x = self.main_widget.x() + self.main_widget.width()

            if (
                self.main_widget.output_window_y + output_window.height()
                > screen_geometry.height() - SCREEN_MARGIN
            ):
                self.main_widget.output_window_y = self.main_widget.y()

        else:
            self.main_widget.output_window_x, self.main_widget.output_window_y = (
                self.main_widget.open_window_positions.pop(0)
            )

        output_window.move(self.main_widget.output_window_x, self.main_widget.output_window_y)
        output_window.resize(MINIMUM_WIDTH, output_window.height())
        output_window.setMinimumWidth(MINIMUM_WIDTH)

        output_window.destroyed.connect(
            lambda: self.main_widget.open_window_positions.append(
                (self.main_widget.output_window_x, self.main_widget.output_window_y)
            )
        )


class RedisMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.init_classes()
        self.ui_setup.setup_ui()

        self.reorder_channels = True
        self.subscriber = None

    def init_classes(self):
        self.ui_setup = UISetup(self)
        self.channel_manager = ChannelManager(self)
        self.window_manager = OutputWindowManager(self)
        self.subscriber = None
        self.output_windows = {}
        self.open_window_positions = []

    def toggle_reorder(self):
        self.reorder_channels = not self.reorder_channels

    def start_monitoring(self):
        redis_url = self.ui_setup.redis_url_input.text()
        channel_pattern = self.ui_setup.channel_pattern_input.text()
        self.subscriber = RedisSubscriber(redis_url, channel_pattern)
        self.subscriber.new_channel.connect(self.channel_manager.add_channel)
        self.subscriber.start()
        self.status_bar.showMessage("Status: Monitoring")

    def stop_monitoring(self):
        if self.subscriber:
            self.subscriber.terminate()
            self.status_bar.showMessage("Status: Not Monitoring")

    def open_output_window(self, item: QListWidgetItem):
        self.window_manager.open_output_window(item)

    def closeEvent(self, event):
        for window in self.output_windows.values():
            window.close()
        event.accept()
