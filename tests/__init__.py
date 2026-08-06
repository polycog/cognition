"""
Testing config
"""

import logging

# ===

# global logging config
logging.basicConfig(
    level=logging.CRITICAL, format="%(name)s\t%(levelname)s\t%(message)s"
)

# specific module config
# logging.getLogger("cognition.decision").setLevel(logging.INFO)
