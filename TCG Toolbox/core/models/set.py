from dataclasses import dataclass, field
from typing import List, Optional
from .card import Card

@dataclass
class Set:
    id: str
    code: str
    name: str
    released_at: Optional[str] = None
    search_uri: Optional[str] = None
    cards: List[Card] = field(default_factory=list)
    cards_loaded: bool = False
