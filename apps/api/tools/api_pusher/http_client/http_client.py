"""
HTTP requests management
"""

import json
import logging
from urllib import error, request


def _build_request(url: str, method: str, headers: dict, body: bytes):
    """Build an HTTP request."""
    req = request.Request(url=url, data=body, headers=headers or {}, method=method)
    return req


def send_json(
    url: str,
    payload: list | dict,
    headers: dict,
    timeout: int,
    method: str = "POST",
) -> dict:
    """
    Send JSON payload to an API.

    :param url: API endpoint
    :param payload: JSON payload (list or dict)
    :param headers: Request headers
    :param timeout: Request timeout in seconds
    :param method: HTTP method
    :return: Response dict with status, body, headers
    """
    data_bytes = json.dumps(payload).encode("utf-8")
    hdrs = dict(headers) if headers else {}
    hdrs.setdefault("Content-Type", "application/json")

    logging.debug(f"Payload {payload}")

    try:
        req = _build_request(url, method, hdrs, data_bytes)
        logging.info(f"Send {method} to {url}")
        logging.debug(f"Request {req}")

        with request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")
            logging.info(f"HTTP answer {status}")
            logging.debug(f"HTTP answer {body}, Headers: {dict(resp.headers.items())}")
            return {
                "status": status,
                "body": body,
                "headers": dict(resp.headers.items()),
            }
    except error.HTTPError as e:
        content = e.read().decode("utf-8") if e.fp else ""
        logging.error(f"HTTPError {e.code}: {content}")
        raise
    except error.URLError as e:
        logging.error(f"URLError: {e}")
        raise
    except Exception:
        logging.exception("Unknown error")
        raise
