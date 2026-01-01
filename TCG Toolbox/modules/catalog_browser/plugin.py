from PySide6.QtCore import Qt
from modules.catalog_browser.panel import CatalogBrowserPanel


def register(main_window):
    panel = CatalogBrowserPanel()
    main_window.add_dock("Catalog Browser", panel, area=Qt.LeftDockWidgetArea)
