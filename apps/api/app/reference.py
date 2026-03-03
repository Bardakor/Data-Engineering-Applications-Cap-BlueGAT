"""Reference data loaded from config. No hardcoded data."""

import json
from datetime import date, timedelta
from pathlib import Path

_PATH = Path(__file__).resolve().parent / "data" / "reference.json"

with open(_PATH, encoding="utf-8") as _f:
    _data = json.load(_f)

COUNTRY_REFERENCE: dict = _data["countries"]
REGION_HUBS: dict = _data["region_hubs"]
PRODUCT_PRICES: dict = _data["product_prices"]
CAMPAIGN_PRODUCT_MAP: dict = _data["campaign_product_map"]
POSITIVE_FRAGMENTS: list[str] = _data["seed_fragments"]["positive"]
NEGATIVE_FRAGMENTS: list[str] = _data["seed_fragments"]["negative"]
NEUTRAL_FRAGMENTS: list[str] = _data["seed_fragments"]["neutral"]
TOPIC_KEYWORDS: set[str] = set(_data["topic_keywords"])
STOPWORDS: set[str] = set(_data["stopwords"])

DEFAULT_DATE_FROM: str = (date.today() - timedelta(days=180)).isoformat()
DEFAULT_DATE_TO: str = date.today().isoformat()
