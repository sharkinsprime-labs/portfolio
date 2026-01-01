import sys
import logging
import threading
from pathlib import Path
from datetime import datetime
from shutil import copy2

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import QTimer

from ui.main_window import MainWindow
from modules.logger.plugin import register as register_logger

from core.log_stream import QueueLogHandler
from providers.scryfall.ingest import run_scryfall_sets_cards
from modules.catalog_browser.plugin import register as register_catalog_browser


DEFAULT_LOG_LEVEL = "DEBUG"  # INFO for quieter runs


def _install_file_logging() -> Path:
    log_dir = Path.home() / ".tcg_toolbox"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def setup_logging(log_file: Path):
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    root = logging.getLogger()
    root.setLevel(DEFAULT_LOG_LEVEL)

    # Prevent duplicates if you rerun in IDE
    root.handlers = []

    # UI queue handler
    qh = QueueLogHandler()
    qh.setLevel(logging.NOTSET)
    qh.setFormatter(fmt)
    root.addHandler(qh)

    # File handler (full fidelity)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.NOTSET)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Silence noisy libs if you run DEBUG
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1200, 800)

    # Register Logger dock first (so UI exists)
    register_logger(window)
    register_catalog_browser(window)

    log_file = _install_file_logging()
    setup_logging(log_file)

    log = logging.getLogger("TCG Toolbox")
    log.info("Logger pipeline online")
    log.info(f"File log: {log_file}")

    # Background threads storage (keep alive)
    window._bg_threads = []

    def start_scryfall_ingest():
        log.info("Menu action: syncing Scryfall cache")
        window.statusBar().showMessage("Syncing Scryfall cache...")

        def _target():
            try:
                run_scryfall_sets_cards(max_sets=5, throttle_seconds=0.12)
            except Exception:
                log.exception("Scryfall ingest thread crashed unexpectedly")

        t = threading.Thread(target=_target, daemon=True)
        window._bg_threads.append(t)
        t.start()

    def save_log_snapshot():
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            src = log_file
            dst_dir = Path.home() / ".tcg_toolbox" / "log_snapshots"
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f"app_{ts}.log"
            copy2(src, dst)
            log.info(f"Saved log snapshot: {dst}")
            window.statusBar().showMessage(f"Saved log snapshot: {dst}")
        except Exception:
            log.exception("Failed to save log snapshot")
            window.statusBar().showMessage("Failed to save log snapshot (see app.log)")

    # Menu actions
    run_ingest_action = QAction("Sync Scryfall Cache (sets/cards)", window)
    run_ingest_action.triggered.connect(start_scryfall_ingest)
    window.file_menu.addAction(run_ingest_action)

    save_snapshot_action = QAction("Save Log Snapshot", window)
    save_snapshot_action.triggered.connect(save_log_snapshot)
    window.file_menu.addAction(save_snapshot_action)

    # Status polling (no Qt from worker threads)
    def poll_threads():
        window._bg_threads[:] = [t for t in window._bg_threads if t.is_alive()]
        if not window._bg_threads:
            window.statusBar().showMessage("Ready")

    status_timer = QTimer(window)
    status_timer.setInterval(200)
    status_timer.timeout.connect(poll_threads)
    status_timer.start()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
