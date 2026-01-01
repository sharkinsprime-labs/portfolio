from PySide6.QtCore import Qt
from modules.logger.panel import LogPanel


def register(main_window):
    panel = LogPanel()
    main_window.add_dock("Logger", panel, area=Qt.BottomDockWidgetArea)
