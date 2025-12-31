import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread
from ui.main_window import MainWindow
from core.logbus import install_qt_logging
from modules.logger.plugin import register as register_logger
from providers.demo_ingest import DemoIngestWorker

def main():
    app = QApplication(sys.argv)

    #route python logging -> qt signal -> logger panel
    install_qt_logging()
    log = logging.getLogger('TCG Toolbox')
    log.setLevel(logging.INFO)

    window = MainWindow()
    window.resize(1200, 800)

    #ergister modules (MVP: logger only)
    register_logger(window)

    window.show()

    #demo ingestion runs in a background thread so ui stays responsive
    worker = DemoIngestWorker()
    thread = QThread()
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()