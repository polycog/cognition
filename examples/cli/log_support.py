"""
Some example logging
"""

import logging

import colorlog

# ===


def setup_logging() -> None:
    """call once to setup!"""

    handler = logging.FileHandler("_log.txt", mode="w", encoding="UTF-8")
    handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt="%(log_color)s%(levelname)s\t%(name)s\t%(asctime)s\t%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger = logging.getLogger("cognition.decision")
    logger.setLevel(colorlog.INFO)
    logger.addHandler(handler)
