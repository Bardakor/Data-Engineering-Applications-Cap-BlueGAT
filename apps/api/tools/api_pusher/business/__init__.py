# Global value: Allowed Comments
import time

allowed_comments = [
    "Great campaign!",
    "Not very engaging.",
    "Loved the product presentation.",
    "Too many details, hard to follow.",
    "Creative and fun approach!",
    "Clear and concise message.",
    "Excellent marketing strategy.",
    "Could be better organized.",
    "Excellente campagne !",
    "Pas très engageant.",
    "J'ai adoré la présentation du produit.",
    "Trop de détails, difficile à suivre.",
    "Approche créative et amusante !",
    "Message clair et concis.",
    "Excellente stratégie marketing.",
    "Pourrait être mieux organisé.",
    "बेहतरीन अभियान!",
    "इतना आकर्षक नहीं।",
    "मुझे उत्पाद की प्रस्तुति बहुत पसंद आई।",
    "बहुत ज़्यादा विवरण हैं, समझना मुश्किल है।",
    "रचनात्मक और मज़ेदार तरीका!",
    "स्पष्ट और संक्षिप्त संदेश।",
    "उत्कृष्ट विपणन रणनीति।",
    "इसे और बेहतर तरीके से संगठित किया जा सकता है।",
    "很棒的活动！",
    "不太有吸引力。",
    "很喜欢产品的展示。",
    "细节太多，难以跟上。",
    "有创意又有趣的方法！",
    "信息清晰简洁。",
    "出色的营销策略。",
    "组织得可以更好一些。",
    "素晴らしいキャンペーンです！",
    "あまり惹きつけられないです。",
    "製品のプレゼンテーションがとても良かったです。",
    "詳細が多すぎて、ついていくのが大変です。",
    "創造的で楽しいアプローチです！",
    "明確で簡潔なメッセージです。",
    "優れたマーケティング戦略です。",
    "もっと整理できると思います。",
]

allowed_countries = [
    "France",
    "Germany",
    "Brazil",
    "UK",
    "Japan",
    "China",
    "India",
    "USA",
    "Canada",
]

allowed_products = [
    "Fried Wings",
    "Chicken Nuggets",
    "Grilled Tenders",
    "Spicy Strips",
    "Hardcore Spicy Tenders",
    "Soft Chicken Nuggets",
    "Too Much Grilled Tenders",
]


def str_time_prop(start: str, end: str, time_format: str, prop: float) -> str:
    """Get a time at a proportion of a range of two formatted times."""
    import time as _time

    stime = _time.mktime(_time.strptime(start, time_format))
    etime = _time.mktime(_time.strptime(end, time_format))
    ptime = stime + prop * (etime - stime)
    return _time.strftime(time_format, _time.localtime(ptime))


def random_date(start: str, end: str, prop: float) -> str:
    """Get a random date between start and end."""
    return str_time_prop(start, end, "%Y-%m-%d", prop)
