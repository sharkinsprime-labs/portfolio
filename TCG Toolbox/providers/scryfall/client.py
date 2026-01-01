import requests


class ScryfallClient:
    BASE = "https://api.scryfall.com"

    def __init__(self, user_agent: str = "TCG Toolbox (dev)"):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json;q=0.9,*/*;q=0.8",
        })

    def list_sets(self) -> dict:
        return self._get_json(f"{self.BASE}/sets")

    def get_page(self, url: str) -> dict:
        return self._get_json(url)

    def _get_json(self, url: str) -> dict:
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
