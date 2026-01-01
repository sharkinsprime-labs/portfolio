import time

from core.log import get_logger
from providers.scryfall.client import ScryfallClient


def run_scryfall_sets_cards(max_sets: int = 5, throttle_seconds: float = 0.12):
    """
    Ingest sets -> cards using Scryfall set search_uri pages.

    NOTE: We intentionally sample card-name logging to keep UI stable.
    Full fidelity details still go to app.log via log.exception().
    """
    log = get_logger("ingest.scryfall")
    log.info("Scryfall ingest starting")

    client = ScryfallClient(user_agent="TCG Toolbox (Scryfall ingest)")
    payload = client.list_sets()
    sets = payload.get("data", [])

    if max_sets and max_sets > 0:
        sets = sets[:max_sets]

    log.info(f"Fetched {len(sets)} sets to process")

    for s in sets:
        set_name = s.get("name", "Unknown Set")
        search_uri = s.get("search_uri")
        if not search_uri:
            log.warning(f"Skipping set with no search_uri: {set_name}")
            continue

        log.info(f"Set start: {set_name}")

        page_url = search_uri
        count = 0

        while page_url:
            try:
                page = client.get_page(page_url)
            except Exception:
                # Full details go to file log; UI will show a short line
                log.exception(f"Failed page fetch for set '{set_name}'")
                break

            for card in page.get("data", []):
                count += 1
                card_name = card.get("name", "Unknown Card")

                # Sample output (first 10 + every 50th) to keep UI from melting
                if count <= 10 or count % 50 == 0:
                    log.info(f"{set_name} : {card_name}")

            if page.get("has_more"):
                page_url = page.get("next_page")
                time.sleep(throttle_seconds)
            else:
                page_url = None

        log.info(f"{set_name} : processed {count} cards")

    log.info("Scryfall ingest complete")