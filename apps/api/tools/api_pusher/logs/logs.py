"""
Log file management
"""

import logging
import sys


def compute_log_level(log_level: str) -> int:
    """
    Compute numeric log level from string (DEBUG, INFO, ERROR).

    :param log_level: String for log levels
    :return: Int representing the log level to apply
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        logging.error(f"Invalid log level: {log_level}")
        sys.exit(5)
    return numeric_level
