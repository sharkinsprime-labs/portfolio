from __future__ import annotations

from typing import Callable, Generic, List, Optional, TypeVar
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

T = TypeVar("T")


class SimpleListModel(QAbstractListModel, Generic[T]):
    """
    Reusable list model:
      - items: list[T]
      - display_fn: T -> str
      - tooltip_fn: T -> str (optional)
    """

    def __init__(
        self,
        items: Optional[List[T]] = None,
        display_fn: Optional[Callable[[T], str]] = None,
        tooltip_fn: Optional[Callable[[T], str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._items: List[T] = list(items or [])
        self._display_fn = display_fn or (lambda x: str(x))
        self._tooltip_fn = tooltip_fn  # optional

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        item = self._items[index.row()]

        if role == Qt.DisplayRole:
            return self._display_fn(item)

        # MVP hover support
        if role == Qt.ToolTipRole and self._tooltip_fn is not None:
            return self._tooltip_fn(item)

        return None

    def item_at(self, row: int) -> T:
        return self._items[row]

    def set_items(self, items: Optional[List[T]]) -> None:
        self.beginResetModel()
        self._items = list(items or [])
        self.endResetModel()
