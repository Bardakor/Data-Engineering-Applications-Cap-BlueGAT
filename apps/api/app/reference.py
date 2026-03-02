from datetime import date, timedelta

COUNTRY_REFERENCE = {
    "France": {"region": "Europe", "lat": 48.8566, "lng": 2.3522},
    "Germany": {"region": "Europe", "lat": 51.1657, "lng": 10.4515},
    "United States": {"region": "North America", "lat": 37.0902, "lng": -95.7129},
    "Mexico": {"region": "North America", "lat": 23.6345, "lng": -102.5528},
    "Brazil": {"region": "Latin America", "lat": -14.2350, "lng": -51.9253},
    "India": {"region": "Asia-Pacific", "lat": 20.5937, "lng": 78.9629},
    "Japan": {"region": "Asia-Pacific", "lat": 36.2048, "lng": 138.2529},
    "Australia": {"region": "Asia-Pacific", "lat": -25.2744, "lng": 133.7751},
    "United Arab Emirates": {
        "region": "Middle East & Africa",
        "lat": 23.4241,
        "lng": 53.8478,
    },
    "South Africa": {
        "region": "Middle East & Africa",
        "lat": -30.5595,
        "lng": 22.9375,
    },
}

REGION_HUBS = {
    "Europe": {"lat": 50.1109, "lng": 8.6821, "label": "Europe Hub"},
    "North America": {"lat": 39.0997, "lng": -94.5786, "label": "North America Hub"},
    "Latin America": {"lat": -23.5505, "lng": -46.6333, "label": "Latin America Hub"},
    "Asia-Pacific": {"lat": 28.6139, "lng": 77.2090, "label": "Asia-Pacific Hub"},
    "Middle East & Africa": {"lat": 25.2048, "lng": 55.2708, "label": "MEA Hub"},
}

PRODUCT_PRICES = {
    "Chicken Nuggets": 10.5,
    "Spicy Strips": 11.8,
    "Veggie Bites": 9.9,
    "Hot Wings": 12.2,
    "Classic Wraps": 8.9,
}

CAMPAIGN_PRODUCT_MAP = {
    "CAMP012": "Chicken Nuggets",
    "CAMP013": "Chicken Nuggets",
    "CAMP019": "Spicy Strips",
    "CAMP021": "Spicy Strips",
    "CAMP024": "Veggie Bites",
    "CAMP028": "Veggie Bites",
    "CAMP031": "Hot Wings",
    "CAMP033": "Hot Wings",
    "CAMP040": "Classic Wraps",
    "CAMP042": "Classic Wraps",
}

POSITIVE_FRAGMENTS = [
    "The promo felt clear, premium, and worth repeating.",
    "Great value perception and the product quality landed really well.",
    "The campaign made the meal feel exciting without being confusing.",
    "Fresh, crispy, and very easy to understand from the first screen.",
]

NEGATIVE_FRAGMENTS = [
    "The store ran out too early and the campaign promise felt broken.",
    "Checkout was confusing and the promo code flow killed momentum.",
    "Queue time and slow service made the promotion frustrating.",
    "The creative was strong but operational execution did not keep up.",
]

NEUTRAL_FRAGMENTS = [
    "The campaign was interesting but not every detail was obvious.",
    "Solid product, although the message could be sharper in the app.",
    "I noticed the offer but needed more clarity around the final step.",
    "The promotion worked, yet the experience was not very memorable.",
]

TOPIC_KEYWORDS = {
    "value",
    "crispy",
    "fresh",
    "checkout",
    "sauce",
    "queue",
    "stockout",
    "promo",
    "family",
    "service",
    "delivery",
    "app",
    "price",
    "packaging",
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "was",
    "were",
    "from",
    "into",
    "very",
    "felt",
    "made",
    "have",
    "just",
    "really",
    "about",
    "around",
    "your",
    "their",
    "there",
    "they",
    "them",
    "would",
    "could",
    "should",
    "more",
    "less",
    "some",
    "when",
    "what",
    "where",
    "after",
    "before",
    "during",
    "then",
    "than",
    "into",
    "onto",
    "meal",
    "offer",
}

DEFAULT_DATE_FROM = (date.today() - timedelta(days=180)).isoformat()
DEFAULT_DATE_TO = date.today().isoformat()
