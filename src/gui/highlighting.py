# src/gui/highlighting.py

from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor


class Highlighter:
    @staticmethod
    def highlight_item(item: QListWidgetItem):
        start_color = QColor("yellow")
        end_color = QColor("white")

        item.setBackground(start_color)

        duration = 800
        interval = 50

        steps = duration // interval
        delta_r = (end_color.red() - start_color.red()) / steps
        delta_g = (end_color.green() - start_color.green()) / steps
        delta_b = (end_color.blue() - start_color.blue()) / steps

        current_step = 0

        def update_color():
            nonlocal current_step
            if current_step <= steps:
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
