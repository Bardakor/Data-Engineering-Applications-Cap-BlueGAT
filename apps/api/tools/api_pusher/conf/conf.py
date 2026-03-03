"""
Config file management
"""

import configparser
import logging
import sys


def load_config(config_file: str) -> tuple:
    """
    Read parameters from config file and return as tuple.

    :param config_file: Path to the configuration file
    :return: Tuple of configuration values
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        if not config.sections():
            raise ValueError("Empty or invalid config file")

        api_endpoint_url = config["API"]["endpoint_url"]
        api_rest_method = config["API"]["method"]
        api_timeout_seconds = int(config["API"]["timeout_seconds"])

        api_auth_active = config["API_AUTH"]["active"]
        api_username = config["API_AUTH"]["username"]
        api_password = config["API_AUTH"]["password"]

        sales_csv_file_name = config["CSV"]["sales_file_name"]
        sales_csv_file_path = config["CSV"]["sales_file_path"]
        sales_csv_file = sales_csv_file_path + sales_csv_file_name

        campaign_product_csv_file_name = config["CSV"]["campaign_product_file_name"]
        campaign_product_csv_file_path = config["CSV"]["campaign_product_file_path"]
        campaign_product_csv_file = campaign_product_csv_file_path + campaign_product_csv_file_name

        ollama_url = config["OLLAMA"]["ollama_url"]
        ollama_model = config["OLLAMA"]["ollama_model"]

        log_file = config["LOG"]["log_file"]
        log_level = config["LOG"]["log_level"]
        log_format = config["LOG"]["log_format"]

        generation_mode = config["GENERATION"]["mode"]

        return (
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
        )
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_file}")
        logging.exception(f"Config file not found: {config_file}")
        sys.exit(5)
    except configparser.Error as e:
        logging.error(f"Error when reading config file: {e}")
        logging.exception(f"Error when reading config file: {e}")
        sys.exit(5)
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        logging.exception(f"Configuration error: {e}")
        sys.exit(5)
