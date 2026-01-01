from collections import deque
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QCheckBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from core.log_stream import LOG_QUEUE


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.min_level = "ALL"
        self.auto_scroll = True

        # keep last 10k for filtering/redraw
        self._log_buffer = deque(maxlen=10000)  # holds (level, line)

        # pending UI items (level, line)
        self._pending = []
        self._dropped = 0
        self._max_pending = 5000

        # keep visible list bounded
        self._max_visible = 2000

        self.level_order = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
        self.level_colors = {
            "DEBUG": QColor("#888888"),
            "INFO": None,
            "WARNING": QColor("#d1a800"),
            "ERROR": QColor("#d84315"),
            "CRITICAL": QColor("#b00020"),
        }

        # UI list (no QTextDocument, much more stable)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.NoSelection)
        self.list.setUniformItemSizes(True)
        self.list.setWordWrap(False)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_logs)

        snapshot_btn = QPushButton("Snapshot")
        snapshot_btn.clicked.connect(self._save_snapshot_clicked)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setCurrentText(self.min_level)
        self.level_combo.currentTextChanged.connect(self._on_level_changed)

        self.autoscroll_cb = QCheckBox("Autoscroll")
        self.autoscroll_cb.setChecked(self.auto_scroll)
        self.autoscroll_cb.stateChanged.connect(self._on_autoscroll_changed)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.level_combo)
        btn_row.addWidget(self.autoscroll_cb)
        btn_row.addStretch(1)
        btn_row.addWidget(snapshot_btn)
        btn_row.addWidget(clear_btn)

        layout = QVBoxLayout()
        layout.addLayout(btn_row)
        layout.addWidget(self.list)
        self.setLayout(layout)

        # Timer: drain queue + flush UI
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        # immediate startup line
        self._enqueue_ui("INFO", "Logger panel connected")

    # ---------- snapshot ----------
    def save_snapshot(self) -> str:
        out_dir = Path.home() / ".tcg_toolbox" / "log_snapshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"ui_buffer_{ts}.txt"

        with out_path.open("w", encoding="utf-8") as f:
            for lvl, line in self._log_buffer:
                f.write(line + "\n")

        return str(out_path)

    def _save_snapshot_clicked(self):
        path = self.save_snapshot()
        self._enqueue_ui("INFO", f"Saved UI snapshot: {path}")

    # ---------- filtering ----------
    def _on_level_changed(self, new_level: str):
        self.min_level = new_level
        self._redraw_from_buffer()

    def _on_autoscroll_changed(self, state: int):
        self.auto_scroll = (state == Qt.Checked)

    def _detect_level(self, line: str) -> str:
        detected = "INFO"
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            candidate = parts[1].upper().strip()
            if candidate in self.level_order:
                detected = candidate
        return detected

    def _passes_filter(self, level: str) -> bool:
        if self.min_level == "ALL":
            return True
        return self.level_order[level] == self.level_order[self.min_level]

    def _make_item(self, level: str, line: str) -> QListWidgetItem:
        item = QListWidgetItem(line)
        color = self.level_colors.get(level)
        if color is not None:
            item.setForeground(color)
        return item

    def _redraw_from_buffer(self):
        self.list.setUpdatesEnabled(False)
        self.list.clear()

        buf = list(self._log_buffer)
        if len(buf) > self._max_visible:
            buf = buf[-self._max_visible:]

        for lvl, line in buf:
            if self._passes_filter(lvl):
                self.list.addItem(self._make_item(lvl, line))

        self.list.setUpdatesEnabled(True)
        if self.auto_scroll:
            self.list.scrollToBottom()

    # ---------- ingestion from queue ----------
    def _enqueue_ui(self, level: str, line: str):
        """Internal messages that bypass LOG_QUEUE."""
        self._log_buffer.append((level, line))
        if self._passes_filter(level):
            if len(self._pending) >= self._max_pending:
                self._dropped += 1
                return
            self._pending.append((level, line))

    def _tick(self):
        # Drain global log queue into our buffer/pending
        DRAIN = 500
        for _ in range(DRAIN):
            try:
                msg = LOG_QUEUE.get_nowait()
            except Exception:
                break
            self._handle_log_line(msg)

        # Flush pending items to UI
        self._flush_pending()

    def _handle_log_line(self, line: str):
        # Keep UI safe
        MAX_LEN = 500
        if len(line) > MAX_LEN:
            line = line[:MAX_LEN] + " …(truncated; see app.log)"

        level = self._detect_level(line)

        # Avoid big ERROR blobs in UI (file log has full traceback)
        if level in {"ERROR", "CRITICAL"} and len(line) > 300:
            line = line[:300] + " …(see app.log)"

        self._log_buffer.append((level, line))

        if not self._passes_filter(level):
            return

        if len(self._pending) >= self._max_pending:
            self._dropped += 1
            return

        self._pending.append((level, line))

    def _flush_pending(self):
        if not self.isVisible():
            self._pending.clear()
            return
        if not self._pending and self._dropped == 0:
            return

        self.list.setUpdatesEnabled(False)

        BATCH = 200
        chunk = self._pending[:BATCH]
        del self._pending[:BATCH]

        overflow = (self.list.count() + len(chunk)) - self._max_visible
        if overflow > 0:
            for _ in range(overflow):
                item = self.list.takeItem(0)
                del item

        for lvl, line in chunk:
            self.list.addItem(self._make_item(lvl, line))

        if self._dropped > 0:
            summary = f"[UI] Dropped {self._dropped} lines due to high rate (see app.log for full output)"
            self.list.addItem(self._make_item("WARNING", summary))
            self._dropped = 0

        self.list.setUpdatesEnabled(True)
        if self.auto_scroll:
            self.list.scrollToBottom()

    def _clear_logs(self):
        self._log_buffer.clear()
        self._pending.clear()
        self._dropped = 0
        self.list.clear()
