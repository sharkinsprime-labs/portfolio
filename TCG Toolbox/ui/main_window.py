from PySide6.QtWidgets import QMainWindow, QDockWidget, QStatusBar, QWidget
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TCG Toolbox")

        # Dock registry so we can re-open panels from the View menu
        self._dock_actions = {}   # title -> QAction
        self._docks = {}          # title -> QDockWidget

        # Menu bar
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu("File")
        self.view_menu = menubar.addMenu("View")

        # Status bar (bottom)
        sb = QStatusBar(self)
        sb.setSizeGripEnabled(True)
        sb.showMessage("Ready")
        self.setStatusBar(sb)

        # Central workspace (keeps main window "real" even if all docks float)
        self.setCentralWidget(QWidget(self))

    def add_dock(self, title: str, widget, area=Qt.LeftDockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(area, dock)

        # Track dock
        self._docks[title] = dock

        # Create (or reuse) a checkable View menu action
        if title not in self._dock_actions:
            action = QAction(title, self)
            action.setCheckable(True)
            action.setChecked(True)

            # Menu -> dock
            action.toggled.connect(dock.setVisible)

            # Dock -> menu (when user closes it)
            dock.visibilityChanged.connect(action.setChecked)

            self.view_menu.addAction(action)
            self._dock_actions[title] = action
        else:
            # If a dock with same title is re-registered, rewire it
            action = self._dock_actions[title]
            action.toggled.connect(dock.setVisible)
            dock.visibilityChanged.connect(action.setChecked)

        return dock