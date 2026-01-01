from __future__ import annotations
from typing import Optional

from core.models import Game, Set, Card
from providers.scryfall.client import ScryfallClient


class ScryfallRepository:
    """
    Scryfall -> populates a Game(Set(Card)).
    """

    def __init__(self):
        self.client = ScryfallClient(user_agent="TCG Toolbox (Catalog Browser)")

    def load_mtg_sets(self) -> Game:
        payload = self.client.list_sets()

        game = Game(id="mtg", name="Magic: The Gathering")

        for s in payload.get("data", []):
            set_obj = Set(
                id=s.get("id", ""),
                code=s.get("code", ""),
                name=s.get("name", ""),
                released_at=s.get("released_at"),
                search_uri=s.get("search_uri", None),
            )

            if set_obj.code:
                game.add_set(set_obj)

        return game

    def load_cards_for_set(self, set_obj: Set) -> None:
        """
        Mutates set_obj: fills cards + sets cards_loaded=True.
        Uses search_uri pagination. Safe if a page fails (partial results ok for MVP).
        """
        if not set_obj.search_uri:
            set_obj.cards = []
            set_obj.cards_loaded = True
            return

        cards = []
        page_url: Optional[str] = set_obj.search_uri

        while page_url:
            page = self.client.get_page(page_url)

            for c in page.get("data", []):
                cards.append(Card(id=c.get("id", ""), name=c.get("name", "")))

            if page.get("has_more"):
                page_url = page.get("next_page")
            else:
                page_url = None

        set_obj.cards = cards
        set_obj.cards_loaded = True
