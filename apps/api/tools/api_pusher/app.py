"""
Business logic - main functions for api_pusher
"""

import codecs
import json
import logging
from urllib import request

from tools.api_pusher.business.generate_campaign_feedback import (
    generate_feedback_via_ollama,
    generate_random_feedback,
)
from tools.api_pusher.business.generate_sales_file import (
    generate_random_sales,
    generate_sales_via_ollama,
)
from tools.api_pusher.http_client.http_client import send_json


def fetch_valid_feedback_pairs(api_endpoint_url: str, timeout: int) -> list[dict[str, str]]:
    """Fetch (username, campaign_id) pairs from API for enrichment. Returns [] on failure."""
    base = api_endpoint_url.rsplit("/", 1)[0]
    url = f"{base}/feedback-valid-pairs?limit=500"
    try:
        req = request.Request(url=url, method="GET")
        with request.urlopen(req, timeout=timeout) as resp:
            if resp.getcode() == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logging.warning("Could not fetch valid feedback pairs: %s", e)
    return []


def push_campaign_feedbacks_to_api(
    api_endpoint_url: str,
    api_rest_method: str,
    api_timeout_seconds: int,
    api_auth_active: str,
    api_username: str,
    api_password: str,
    generation_mode: str,
    ollama_url: str,
    ollama_model: str,
    feedbacks_to_push: int,
) -> int:
    """Generate feedbacks and push them to the API endpoint."""
    url = api_endpoint_url
    method = api_rest_method
    timeout = api_timeout_seconds
    headers = {}

    if api_auth_active and api_auth_active.lower() == "true":
        logging.debug("Auth (not implemented)")

    payload: list = []
    logging.info(f"Generation mode: {generation_mode}")

    valid_pairs = fetch_valid_feedback_pairs(api_endpoint_url, api_timeout_seconds)
    if valid_pairs:
        logging.info("Using %d valid (username, campaign_id) pairs for enrichment", len(valid_pairs))

    if generation_mode == "ollama":
        logging.info("Local AI generation mode, using Ollama")
        payload = generate_feedback_via_ollama(
            count=feedbacks_to_push,
            model=ollama_model,
            host=ollama_url,
            timeout=300,
            valid_pairs=valid_pairs or None,
        )
    else:
        logging.info("Manual generation mode, using random functions")
        payload = generate_random_feedback(
            feedbacks_to_push,
            payload,
            valid_pairs=valid_pairs or None,
        )

    try:
        resp = send_json(
            url=url,
            payload=payload,
            headers=headers,
            timeout=timeout,
            method=method,
        )
        logging.info("Query finished without error")
        logging.info(json.dumps(resp, indent=2, ensure_ascii=False))
        return 0
    except Exception:
        logging.exception("Error on query")
        return 1


def create_sales_csv_file(
    sales_csv_file: str,
    campaign_product_csv_file: str,
    generation_mode: str,
    ollama_url: str,
    ollama_model: str,
    lines_to_create: int,
) -> None:
    """Generate sales and campaign/product CSVs and write to files."""
    columns_sales = "username,sale_date,country,product,quantity,unit_price,total_amount\n"
    columns_campaign_product = "campaign_id,product\n"

    logging.info(f"Generation mode: {generation_mode}")

    if generation_mode == "ollama":
        logging.info("Local AI generation mode, using Ollama")
        csv_sales, campaign_product_csv = generate_sales_via_ollama(
            lines_to_create=lines_to_create,
            already_existing_sales=columns_sales,
            already_existing_campaign_product=columns_campaign_product,
            model=ollama_model,
            host=ollama_url,
            timeout=300,
        )
    else:
        logging.info("Manual generation mode, using random functions")
        csv_sales, campaign_product_csv = generate_random_sales(
            lines_to_create=lines_to_create,
            already_existing_sales=columns_sales,
            already_existing_campaign_product=columns_campaign_product,
        )

    with codecs.open(sales_csv_file, "w", "utf-8") as f:
        f.write(csv_sales)

    with codecs.open(campaign_product_csv_file, "w", "utf-8") as f:
        f.write(campaign_product_csv)
