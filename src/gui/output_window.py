from PyQt5.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QDialog,
    QTextEdit,
    QPushButton,
    QFileDialog,
)
from PyQt5.QtCore import Qt


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
        self.setWindowFlags(Qt.Tool)

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
