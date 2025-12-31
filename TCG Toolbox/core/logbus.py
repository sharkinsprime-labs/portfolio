import logging
from PySide6.QtCore import QObject, Signal

class LogBus(QObject):
    message = Signal(str)

LOG_BUS = LogBus()

class QtLogHandler(logging.Handler):
    def emit(selfself, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            LOG_BUS.message.emit(msg)
        except Exception:
            #never let logging break the app
            pass

def install_qt_logging() -> None:
    """
    installs a root handler that forwards log records to the qt logbus
    call once at app startup
    """
    handler = QtLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

    root = logging.getLogger()
    #avoid duplicate handlers if re-run in an IDE
    if not any(isinstance(h, QtLogHandler) for h in root.handlers):
        root.addHandler(handler)

    #root can stay WARNING: set your app logger to INFO/DEBUG as needed
    root.setLevel(logging.WARNING)