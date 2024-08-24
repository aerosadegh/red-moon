from typing import TYPE_CHECKING

from PyQt5.QtWidgets import (
    QApplication,
    QListWidgetItem,
)

if TYPE_CHECKING:
    from .main_window import RedisMonitor


class OutputWindowManager:
    def __init__(self, main_widget: "RedisMonitor"):
        self.main_widget = main_widget

    def open_output_window(self, item: QListWidgetItem):
        channel_name = item.text()
        if channel_name not in self.main_widget.output_windows_ui:
            return

        output_window = self.main_widget.output_windows_ui[channel_name]
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

            desktop = QApplication.desktop()
            if desktop is not None:
                screen_geometry = desktop.availableGeometry()
                if (
                    self.main_widget.output_window_x + output_window.width()
                    > screen_geometry.width() - SCREEN_MARGIN
                ):
                    self.main_widget.output_window_x = (
                        self.main_widget.x() + self.main_widget.width()
                    )

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
