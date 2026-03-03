"""
Data Generation management - Campaign feedback
"""

import json
import logging
import random
import urllib.error
import urllib.request

from tools.api_pusher.business import allowed_comments, random_date


def generate_random_feedback(feedbacks_to_push: int, payload: list) -> list:
    """
    Generate random feedbacks.

    :param feedbacks_to_push: number of feedbacks to push
    :param payload: existing payload (list to append to)
    :return: payload with generated feedbacks appended
    """
    result = list(payload)
    for _ in range(feedbacks_to_push):
        user_number = random.randint(1, 4999)
        campaign_date = random_date("2024-1-1", "2026-12-31", random.random())
        campaign_number = random.randint(1, 999)

        comment_number = random.randint(1, len(allowed_comments))
        comment = allowed_comments[comment_number - 1]
        logging.debug(f"Random comment number: {comment_number}, comment: {comment}")

        item_to_add = {
            "username": f"user_{user_number}",
            "feedback_date": campaign_date,
            "campaign_id": f"CAMP{campaign_number:03d}",
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

    user_prompt = f"""
Generate {count} distinct feedback objects as a JSON array.
Rules:
- "username": random usernames like in social network, no obscene name.
- "feedback_date": valid date "YYYY-MM-DD" in the year 2024, 2025 and 2026.
- "campaign_id": "CAMP" followed by three digits (e.g. CAMP147).
- "comment": choose a random number between 0 and {len(allowed_comments) - 1} (index into comments list).
Ensure all items are valid and diverse. Return only JSON.
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

    result = []
    for item in items:
        comment_idx = int(item.get("comment", 0)) % len(allowed_comments)
        result.append(
            {
                "username": str(item["username"]),
                "feedback_date": str(item["feedback_date"]),
                "campaign_id": str(item["campaign_id"]),
                "comment": allowed_comments[comment_idx],
            }
        )
        logging.debug(f"Ollama response item: {result[-1]}")

    return result
