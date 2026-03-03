"""Sentiment analysis."""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_sentiment_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(comment: str) -> tuple[str, float]:
    """Return (label, score) for a comment. Label is positive/neutral/negative."""
    score = _sentiment_analyzer.polarity_scores(comment)["compound"]
    if score >= 0.25:
        return "positive", round(score, 4)
    if score <= -0.15:
        return "negative", round(score, 4)
    return "neutral", round(score, 4)
