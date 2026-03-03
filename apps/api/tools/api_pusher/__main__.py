"""
Entry point for api_pusher - Fake data generator for Data Engineering Applications.
"""

import logging
import sys
from pathlib import Path

from tools.api_pusher.app import create_sales_csv_file, push_campaign_feedbacks_to_api
from tools.api_pusher.conf.conf import load_config
from tools.api_pusher.logs.logs import compute_log_level


def usage() -> None:
    """Print usage message."""
    print("Usage: python -m tools.api_pusher ACTION <count>")
    print()
    print("ACTION:")
    print("  PUSH <count>  - Generate feedbacks and push to API (e.g. PUSH 10)")
    print("  CSV <count>   - Generate sales + campaign_product CSV files (e.g. CSV 10)")
    print()
    print("Examples:")
    print("  cd apps/api && python -m tools.api_pusher PUSH 10")
    print("  cd apps/api && python -m tools.api_pusher CSV 20")


def main(arguments: list[str]) -> int:
    """Main entry point."""
    if len(arguments) < 2:
        usage()
        return 1

    action = arguments[1].upper()

    if action == "HELP" or action == "-H" or action == "--HELP":
        usage()
        return 0

    if len(arguments) < 3:
        usage()
        return 1

    config_path = Path(__file__).resolve().parent / "config.ini"
    if not config_path.exists():
        logging.error(f"Config not found: {config_path}")
        return 1

    (
        api_endpoint_url,
        api_rest_method,
        api_timeout_seconds,
        api_auth_active,
        api_username,
        api_password,
        sales_csv_file,
        campaign_product_csv_file,
        ollama_url,
        ollama_model,
        log_file,
        log_level,
        log_format,
        generation_mode,
    ) = load_config(str(config_path))

    numeric_level = compute_log_level(log_level)
    logging.basicConfig(
        handlers=[
            logging.FileHandler(filename=log_file, encoding="utf-8", mode="a+"),
            logging.StreamHandler(),
        ],
        level=numeric_level,
        format=log_format,
    )
    logging.info("Config file loaded")

    try:
        count = int(arguments[2])
    except ValueError:
        logging.error(f"Invalid count: {arguments[2]}")
        usage()
        return 1

    if action == "PUSH":
        return push_campaign_feedbacks_to_api(
            api_endpoint_url=api_endpoint_url,
            api_rest_method=api_rest_method,
            api_timeout_seconds=api_timeout_seconds,
            api_auth_active=api_auth_active,
            api_username=api_username,
            api_password=api_password,
            generation_mode=generation_mode,
            ollama_url=ollama_url,
            ollama_model=ollama_model,
            feedbacks_to_push=count,
        )
    elif action == "CSV":
        create_sales_csv_file(
            sales_csv_file=sales_csv_file,
            campaign_product_csv_file=campaign_product_csv_file,
            generation_mode=generation_mode,
            ollama_url=ollama_url,
            ollama_model=ollama_model,
            lines_to_create=count,
        )
        logging.info(f"Created {sales_csv_file} and {campaign_product_csv_file}")
        return 0
    else:
        logging.error(f"Unknown action: {action}")
        usage()
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
