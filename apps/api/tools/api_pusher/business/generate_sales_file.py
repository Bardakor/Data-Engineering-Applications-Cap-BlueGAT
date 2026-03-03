"""
Data Generation management - Sales CSV
"""

import json
import logging
import random
import urllib.request

from tools.api_pusher.business import (
    allowed_countries,
    allowed_products,
    random_date,
)


def generate_random_sales(
    lines_to_create: int,
    already_existing_sales: str,
    already_existing_campaign_product: str,
) -> tuple[str, str]:
    """
    Generate random sales and campaign/product mapping.

    :param lines_to_create: number of lines to create
    :param already_existing_sales: existing header for sales CSV
    :param already_existing_campaign_product: existing header for campaign/product CSV
    :return: tuple (sales_csv_content, campaign_product_csv_content)
    """
    result_sales = already_existing_sales
    result_campaign_product = already_existing_campaign_product

    for _ in range(lines_to_create):
        user_number = random.randint(1, 4999)
        sale_date = random_date("2024-1-1", "2026-12-31", random.random())
        quantity = random.randint(1, 999)
        unit_price = round(random.uniform(1.00, 200.00), 2)
        total_amount = round(quantity * unit_price, 2)

        campaign_number = random.randint(1, 999)

        country = random.choice(allowed_countries)
        product = random.choice(allowed_products)

        line_sales = f"user_{user_number},{sale_date},{country},{product},{quantity},{unit_price},{total_amount}\n"
        line_campaign = f"CAMP{campaign_number:03d},{product}\n"

        logging.debug(f"Manual generation, line: {line_sales} & {line_campaign}")
        result_sales += line_sales
        result_campaign_product += line_campaign

    return result_sales, result_campaign_product


def generate_sales_via_ollama(
    lines_to_create: int,
    already_existing_sales: str,
    already_existing_campaign_product: str,
    model: str = "tinyllama",
    host: str = "127.0.0.1:11434",
    temperature: float = 0.7,
    timeout: int = 300,
) -> tuple[str, str]:
    """
    Generate sales via Ollama API and convert to CSV.

    :param lines_to_create: number of lines to generate
    :param already_existing_sales: CSV header for sales
    :param already_existing_campaign_product: CSV header for campaign/product
    :param model: Ollama model name
    :param host: Ollama base URL
    :param temperature: model creativity
    :param timeout: HTTP timeout in seconds
    :return: tuple (sales_csv, campaign_product_csv)
    """
    result_sales = already_existing_sales
    result_campaign_product = already_existing_campaign_product

    if lines_to_create <= 0:
        return result_sales, result_campaign_product

    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "sale_date": {
                    "type": "string",
                    "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                },
                "campaign_id": {"type": "string"},
                "product_id": {"type": "integer"},
                "country_id": {"type": "integer"},
                "quantity": {"type": "integer"},
                "unit_price_part1": {"type": "integer"},
                "unit_price_part2": {"type": "integer"},
            },
            "required": [
                "username",
                "sale_date",
                "campaign_id",
                "product_id",
                "country_id",
                "quantity",
                "unit_price_part1",
                "unit_price_part2",
            ],
            "additionalProperties": False,
        },
        "minItems": lines_to_create,
        "maxItems": lines_to_create,
    }

    system_prompt = (
        "You are a data generator. Output strictly JSON that matches the schema. "
        "Do not include explanations or extra text."
    )

    user_prompt = f"""
Generate {lines_to_create} distinct sales as a JSON array.
Rules:
- "username": random usernames like in social network, no obscene name.
- "sale_date": valid date "YYYY-MM-DD" in the year 2024, 2025 and 2026.
- "campaign_id": "CAMP" followed by three digits (e.g. CAMP147).
- "product_id": random number between 0 and {len(allowed_products) - 1}
- "country_id": random number between 0 and {len(allowed_countries) - 1}
- "quantity": random number between 1 and 1000
- "unit_price_part1": random number between 1 and 199
- "unit_price_part2": random number between 1 and 99
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

    for item in items:
        username = item.get("username", "user_0")
        sale_date = item["sale_date"]
        campaign_id = item["campaign_id"]
        country = allowed_countries[int(item.get("country_id", 0)) % len(allowed_countries)]
        product = allowed_products[int(item.get("product_id", 0)) % len(allowed_products)]
        quantity = item.get("quantity", 1)
        unit_price = round(
            item.get("unit_price_part1", 10) + (item.get("unit_price_part2", 0) / 100),
            2,
        )
        total_amount = round(quantity * unit_price, 2)

        line_sales = f"{username},{sale_date},{country},{product},{quantity},{unit_price},{total_amount}\n"
        line_campaign = f"{campaign_id},{product}\n"

        logging.debug(f"Ollama response line: {line_sales} & {line_campaign}")
        result_sales += line_sales
        result_campaign_product += line_campaign

    return result_sales, result_campaign_product
