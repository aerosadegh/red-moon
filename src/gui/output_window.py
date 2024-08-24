from PyQt5.QtWidgets import (
    QVBoxLayout,
    QDialog,
    QTextEdit,
    QPushButton,
    QFileDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QFont

from .utils import resource_path


class OutputWindowUI(QDialog):
    def __init__(self, channel_name, parent=None):
        super().__init__(parent)
        self.channel_name = channel_name
        self.message_counter = 0

        self.setWindowTitle(f"Output for {channel_name}")
        layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_content)
        layout.addWidget(self.export_button)

        # Load the monospaced font
        font_id = QFontDatabase.addApplicationFont(
            resource_path("assets/fonts/static/FiraCode-Regular.ttf")
        )
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.monospaced_font = QFont(font_family)


        self.setLayout(layout)
        self.setWindowFlags(Qt.Tool)

    def update_output(self, data: str):
        self.message_counter += 1
        # Create the message number string with bold tags
        message_number = f"<b>{self.message_counter}:</b><br>"
        # Format the data as code with monospaced font and line wrapping
        formatted_data = f"""<span style='font-family: "{self.monospaced_font.family()}";
            white-space: pre-wrap;'>{data}</span>
        """
        self.output_text.append(message_number + formatted_data)


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
