"""
Data Generation management - Campaign feedback
"""

import json
import logging
import random
import urllib.error
import urllib.request

from tools.api_pusher.business import allowed_comments, random_date

# Valid values for Nugget API enrichment (must match reference + seed)
VALID_CAMPAIGN_IDS = (
    "CAMP012", "CAMP013", "CAMP019", "CAMP021", "CAMP024",
    "CAMP028", "CAMP031", "CAMP033", "CAMP040", "CAMP042",
)
VALID_USERNAMES = [f"user{i:03d}" for i in range(1, 361)]


def generate_random_feedback(
    feedbacks_to_push: int,
    payload: list,
    valid_pairs: list[dict[str, str]] | None = None,
) -> list:
    """
    Generate random feedbacks.

    :param feedbacks_to_push: number of feedbacks to push
    :param payload: existing payload (list to append to)
    :param valid_pairs: optional (username, campaign_id) pairs from API for enrichment
    :return: payload with generated feedbacks appended
    """
    result = list(payload)
    rng = random.Random()
    for _ in range(feedbacks_to_push):
        if valid_pairs:
            pair = rng.choice(valid_pairs)
            username, campaign_id = pair["username"], pair["campaign_id"]
        else:
            username = f"user_{rng.randint(1, 4999)}"
            campaign_id = f"CAMP{rng.randint(1, 999):03d}"
        campaign_date = random_date("2024-1-1", "2026-12-31", rng.random())
        comment = rng.choice(allowed_comments)
        item_to_add = {
            "username": username,
            "feedback_date": campaign_date,
            "campaign_id": campaign_id,
            "comment": comment,
        }
        logging.debug(f"Manual generation, item: {item_to_add}")
        result.append(item_to_add)
    return result


def generate_feedback_via_ollama(
    count: int,
    model: str = "tinyllama",
    host: str = "127.0.0.1:11434",
    temperature: float = 0.7,
    timeout: int = 300,
    valid_pairs: list[dict[str, str]] | None = None,
) -> list:
    """
    Generate `count` feedback objects via Ollama API.

    :param count: number of entries to generate
    :param model: model name (e.g. 'tinyllama', 'llama3.2')
    :param host: Ollama base URL (e.g. '127.0.0.1:11434')
    :param temperature: model creativity
    :param timeout: HTTP timeout in seconds
    :return: list of feedback dicts
    """
    if count <= 0:
        return []

    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "feedback_date": {
                    "type": "string",
                    "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                },
                "campaign_id": {"type": "string"},
                "comment": {"type": "integer"},
            },
            "required": ["username", "feedback_date", "campaign_id", "comment"],
            "additionalProperties": False,
        },
        "minItems": count,
        "maxItems": count,
    }

    system_prompt = (
        "You are a data generator. Output strictly JSON that matches the schema. "
        "Do not include explanations or extra text."
    )

    campaigns_str = ", ".join(VALID_CAMPAIGN_IDS)
    user_prompt = f"""
Generate {count} distinct feedback objects as a JSON array.
Rules:
- "username": MUST be one of user001, user002, ... user360 (pick randomly, can repeat).
- "feedback_date": valid date "YYYY-MM-DD" in 2024, 2025 or 2026.
- "campaign_id": MUST be one of: {campaigns_str}
- "comment": integer 0 to {len(allowed_comments) - 1} (index). Use DIFFERENT indices for each item.
Ensure all items are valid. Return only JSON.
"""

    url = f"http://{host}/api/generate"

    ollama_payload = {
        "model": model,
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "format": schema,
        "stream": False,
        "options": {"temperature": temperature},
    }

    logging.debug(f"Schema: {schema}")
    logging.debug(f"URL: {url}")

    try:
        req = urllib.request.Request(
            url=url,
            data=json.dumps(ollama_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            data = json.loads(raw)
    except Exception as e:
        logging.error(f"Ollama call error: {e}")
        raise RuntimeError(f"Ollama call error: {e}") from e

    response = data.get("response")
    if isinstance(response, str):
        try:
            items = json.loads(response)
        except json.JSONDecodeError as e:
            logging.error(f"Non JSON Response: {e}\nContent: {response[:200]}...")
            raise ValueError(f"Non JSON Response: {e}") from e
    else:
        items = response

    rng = random.Random()
    result = []
    used_comment_indices = set()
    for i, item in enumerate(items):
        if valid_pairs:
            pair = rng.choice(valid_pairs)
            username, campaign_id = pair["username"], pair["campaign_id"]
        else:
            username = str(item.get("username", ""))
            if username not in VALID_USERNAMES:
                username = rng.choice(VALID_USERNAMES)
            campaign_id = str(item.get("campaign_id", ""))
            if campaign_id not in VALID_CAMPAIGN_IDS:
                campaign_id = rng.choice(VALID_CAMPAIGN_IDS)
        feedback_date = str(item.get("feedback_date", "2025-01-01"))
        comment_idx = int(item.get("comment", i % len(allowed_comments))) % len(allowed_comments)
        if comment_idx in used_comment_indices and len(used_comment_indices) < len(allowed_comments):
            available = [j for j in range(len(allowed_comments)) if j not in used_comment_indices]
            comment_idx = rng.choice(available) if available else comment_idx
        used_comment_indices.add(comment_idx)
        comment = allowed_comments[comment_idx]
        result.append(
            {
                "username": username,
                "feedback_date": feedback_date,
                "campaign_id": campaign_id,
                "comment": comment,
            }
        )
        logging.debug(f"Ollama response item: {result[-1]}")

    return result
