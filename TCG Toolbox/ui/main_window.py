from PySide6.QtWidgets import QMainWindow, QDockWidget
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TCG Toolbox")

    def add_dock(self, title: str, widget, area=Qt.leftDockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setFeatures(
            QDockWidget.DockWidgetMovable|
            QDockWidget.DockWidgetFloatable|
            QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(area, dock)
        return dock