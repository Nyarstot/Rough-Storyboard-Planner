from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QLabel
)

from source.internal.project import *


class DurationWidget(QWidget):
    def __init__(self, fps=DEFAULT_FPS, parent=None):
        super(DurationWidget, self).__init__(parent)
        
        self.fps = fps
        layout = QHBoxLayout(self)
        self.seconds_edit = QLineEdit("0")
        self.seconds_edit.setFixedWidth(30)
        self.frames_edit = QLineEdit("0")
        self.frames_edit.setFixedWidth(30)
        layout.addWidget(QLabel("("))
        layout.addWidget(self.seconds_edit)
        layout.addWidget(QLabel("+"))
        layout.addWidget(self.frames_edit)
        layout.addWidget(QLabel(")"))
        layout.setContentsMargins(0,0,0,0)
        self.on_change_callbacks = []

        self.seconds_edit.textChanged.connect(self.emit_changed)
        self.frames_edit.textChanged.connect(self.emit_changed)

    def emit_changed(self):
        for callback in self.on_change_callbacks:
            callback()

    def on_value_changed(self, callback):
        self.on_change_callbacks.append(callback)

    def get_duration(self):
        try:
            s = int(self.seconds_edit.text())
        except ValueError:
            s = 0
        try:
            f = int(self.frames_edit.text())
        except ValueError:
            f = 0
        return s, f