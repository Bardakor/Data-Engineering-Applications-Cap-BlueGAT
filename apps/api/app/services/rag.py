"""RAG: retrieval-augmented generation over feedback."""

import json
import logging
import re
import urllib.error
import urllib.request

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Feedback
from app.services.clients import get_openai_client
from app.services.repositories import get_feedback_rows


def build_feedback_document(row: Feedback) -> str:
    """Build searchable text from a feedback row."""
    return (
        f"Campaign {row.campaign_id} for {row.product or 'Unknown product'} in "
        f"{row.country or 'Unknown country'} on {row.feedback_date.isoformat()}. "
        f"Sentiment {row.sentiment_label} ({row.sentiment_score}). Comment: {row.comment}"
    )


def cosine_similarity(query_vector: list[float], candidate_vector: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    query = np.array(query_vector)
    candidate = np.array(candidate_vector)
    denominator = np.linalg.norm(query) * np.linalg.norm(candidate)
    if denominator == 0:
        return 0.0
    return float(np.dot(query, candidate) / denominator)


def ensure_feedback_embeddings(
    session: Session, feedback_rows: list[Feedback], client
) -> None:
    """Compute and persist embeddings for rows that lack them."""
    missing = [row for row in feedback_rows if not row.embedding]
    if not missing:
        return

    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=[build_feedback_document(row) for row in missing],
    )

    for row, embedding_row in zip(missing, response.data, strict=True):
        row.embedding = embedding_row.embedding

    session.commit()


def lexical_score(query: str, row: Feedback) -> float:
    """Fallback lexical overlap score when embeddings unavailable."""
    query_terms = set(re.findall(r"[a-zA-Z']+", query.lower()))
    document_terms = set(re.findall(r"[a-zA-Z']+", build_feedback_document(row).lower()))
    overlap = len(query_terms & document_terms)
    if overlap == 0:
        return 0.0
    return overlap / np.sqrt(len(document_terms))


def answer_without_openai(query: str, citations: list[dict[str, object]]) -> str:
    """Generate answer from citations without LLM."""
    if not citations:
        return "No relevant feedback matched that query in the current filtered dataset."

    from collections import Counter

    by_campaign = Counter(citation["campaignId"] for citation in citations)
    by_country = Counter(citation["country"] for citation in citations)
    by_sentiment = Counter(citation["sentimentLabel"] for citation in citations)

    top_campaign = by_campaign.most_common(1)[0][0]
    top_country = by_country.most_common(1)[0][0]
    top_sentiment = by_sentiment.most_common(1)[0][0]
    examples = "; ".join(citation["comment"] for citation in citations[:2])

    return (
        f"From the retrieved feedback, the main signal is {top_sentiment} sentiment centered on "
        f"{top_campaign} and concentrated in {top_country}. The strongest supporting examples are: {examples}"
    )


def answer_with_ollama(query: str, context: str) -> str | None:
    """Call Ollama chat API. Returns None if unavailable."""
    base = settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/chat"
    payload = {
        "model": settings.ollama_chat_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a retail analytics assistant. Answer only from the supplied feedback snippets. "
                    "Be concise, mention the dominant themes, and do not invent facts."
                ),
            },
            {
                "role": "user",
                "content": f"User question: {query}\n\nEvidence:\n{context}",
            },
        ],
        "stream": False,
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("message", {}).get("content", "").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
        logging.warning("Ollama chat failed: %s", e)
        return None


def run_feedback_rag(session: Session, query: str, filters: dict[str, str]) -> dict[str, object]:
    """Run RAG over feedback: retrieve, optionally embed, and generate answer."""
    feedback_rows = get_feedback_rows(session, filters)
    if not feedback_rows:
        return {
            "answer": "No feedback is available for the selected filters.",
            "retrievalMode": "empty",
            "citations": [],
        }

    client = get_openai_client()
    scored_rows: list[tuple[float, Feedback]] = []

    if client:
        ensure_feedback_embeddings(session, feedback_rows, client)
        query_embedding = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=query,
        ).data[0].embedding
        scored_rows = [
            (cosine_similarity(query_embedding, row.embedding or []), row)
            for row in feedback_rows
        ]
        retrieval_mode = "openai"
    else:
        scored_rows = [(lexical_score(query, row), row) for row in feedback_rows]
        retrieval_mode = "lexical"

    score_by_feedback_id = {row.id: score for score, row in scored_rows}
    top_rows = [
        row
        for score, row in sorted(scored_rows, key=lambda item: item[0], reverse=True)[:5]
        if score > 0
    ]
    citations = [
        {
            "feedbackId": row.id,
            "campaignId": row.campaign_id,
            "product": row.product or "Unknown",
            "country": row.country or "Unknown",
            "feedbackDate": row.feedback_date.isoformat(),
            "sentimentLabel": row.sentiment_label,
            "score": round(score_by_feedback_id.get(row.id, 0.0), 4),
            "comment": row.comment,
        }
        for row in top_rows
    ]

    if client and citations:
        context = "\n\n".join(
            f"[{index + 1}] {build_feedback_document(row)}"
            for index, row in enumerate(top_rows)
        )
        try:
            response = client.responses.create(
                model=settings.openai_rag_model,
                input=(
                    "You are a retail analytics assistant. Answer only from the supplied feedback snippets. "
                    "Be concise, mention the dominant themes, and do not invent facts.\n\n"
                    f"User question: {query}\n\n"
                    f"Evidence:\n{context}"
                ),
            )
            answer = response.output_text
        except AttributeError:
            response = client.chat.completions.create(
                model=settings.openai_rag_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a retail analytics assistant. Answer only from the supplied feedback snippets. "
                            "Be concise, mention the dominant themes, and do not invent facts."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"User question: {query}\n\nEvidence:\n{context}",
                    },
                ],
            )
            answer = response.choices[0].message.content or ""
    elif citations:
        context = "\n\n".join(
            f"[{index + 1}] {build_feedback_document(row)}"
            for index, row in enumerate(top_rows)
        )
        ollama_answer = answer_with_ollama(query, context)
        answer = ollama_answer if ollama_answer else answer_without_openai(query, citations)
    else:
        answer = answer_without_openai(query, citations)

    return {
        "answer": answer,
        "retrievalMode": retrieval_mode,
        "citations": citations,
    }
