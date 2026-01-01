from __future__ import annotations
import logging
import threading
import queue
from typing import Optional

from PySide6.QtWidgets import QWidget, QHBoxLayout, QListView, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt

from core.models import Game, Set, Card
from ui.models.simple_list_model import SimpleListModel
from providers.scryfall.repository import ScryfallRepository


class CatalogBrowserPanel(QWidget):
    """
    Left: Sets (virtualized list)
    Right: Cards (virtualized list)
    Hover: tooltip via ToolTipRole (MVP)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.log = logging.getLogger("TCG Toolbox.catalog")
        self.repo = ScryfallRepository()

        self.game: Optional[Game] = None
        self._loading_set_code: Optional[str] = None
        self._loading_codes: set[str] = set()

        self._uiq: "queue.Queue[tuple]" = queue.Queue()

        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(25)
        self._ui_timer.timeout.connect(self._drain_uiq)
        self._ui_timer.start()

        # Views
        self.sets_view = QListView()
        self.cards_view = QListView()

        # Models (reusable)
        self.sets_model = SimpleListModel[Set](
            items=[],
            display_fn=lambda s: s.name,
            tooltip_fn=lambda s: f"{s.name}\nCode: {s.code}\nReleased: {s.released_at or 'Unknown'}",
        )

        self.cards_model = SimpleListModel[Card](
            items=[],
            display_fn=lambda c: c.name,
            tooltip_fn=lambda c: c.name,  # MVP hover
        )

        self.sets_view.setModel(self.sets_model)
        self.cards_view.setModel(self.cards_model)

        # Layout
        left = QVBoxLayout()
        left.addWidget(QLabel("Sets"))
        left.addWidget(self.sets_view)

        right = QVBoxLayout()
        right.addWidget(QLabel("Cards"))
        right.addWidget(self.cards_view)

        root = QHBoxLayout()
        root.addLayout(left, 1)
        root.addLayout(right, 2)
        self.setLayout(root)

        # Selection handling
        self.sets_view.selectionModel().selectionChanged.connect(self._on_set_selected)

        # Load sets async
        self._load_sets_async()

    def _load_sets_async(self):
        # basic placeholder
        self.sets_model.set_items([])
        self.cards_model.set_items([Card(id="", name="Loading sets…")])

        def worker():
            try:
                game = self.repo.load_mtg_sets()
                self.log.info(f"Loaded {len(game.sets_by_code)} sets into Game(mtg)")
            except Exception as e:
                self.log.exception(f"Failed to load sets: {e}")
                game = None

            self._post_ui(self._apply_game, game)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_game(self, game: Optional[Game]):
        self.game = game
        if not game:
            self.sets_model.set_items([])
            self.cards_model.set_items([Card(id="", name="Failed to load sets (see log)")])
            return

        self.sets_model.set_items(game.sets_sorted())
        self.cards_model.set_items([Card(id="", name="Select a set…")])

    def _on_set_selected(self, selected, deselected):
        indexes = self.sets_view.selectedIndexes()
        if not indexes:
            return

        set_obj = self.sets_model.item_at(indexes[0].row())

        # If already loaded, instant
        if set_obj.cards_loaded:
            self.cards_model.set_items(set_obj.cards)
            return

        # Otherwise load async
        self._loading_set_code = set_obj.code
        self.cards_model.set_items([Card(id="", name=f"Loading cards for {set_obj.name}…")])

        # If already being fetched, don’t start another thread
        if set_obj.code in self._loading_codes:
            return
        self._loading_codes.add(set_obj.code)

        self._load_cards_for_set_async(set_obj)

    def _load_cards_for_set_async(self, set_obj: Set):
        def worker():
            try:
                self.repo.load_cards_for_set(set_obj)
                self.log.info(f"{set_obj.name}: loaded {len(set_obj.cards)} cards")
            except Exception as e:
                self.log.exception(f"Failed to load cards for {set_obj.name}: {e}")
                set_obj.cards = []
                set_obj.cards_loaded = True

            self._post_ui(self._apply_cards, set_obj)
            self._post_ui(self._done_loading_set, set_obj.code)

        threading.Thread(target=worker, daemon=True).start()

    def _done_loading_set(self, code: str):
        self._loading_codes.discard(code)

    def _apply_cards(self, set_obj: Set):
        # Don’t overwrite if user clicked away
        if self._loading_set_code is not None and set_obj.code != self._loading_set_code:
            return

        self._loading_set_code = None  # clear once applied

        if set_obj.cards:
            self.cards_model.set_items(set_obj.cards)
        else:
            self.cards_model.set_items([Card(id="", name="No cards (or fetch error—see log)")])

    def _post_ui(self, fn, *args, **kwargs):
        self._uiq.put((fn, args, kwargs))

    def _drain_uiq(self):
        # bounded drain so we never lock the UI
        for _ in range(200):
            try:
                fn, args, kwargs = self._uiq.get_nowait()
            except queue.Empty:
                return
            try:
                fn(*args, **kwargs)
            except Exception:
                self.log.exception("Catalog UI task failed")


