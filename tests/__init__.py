"""
Testing config
"""

import logging

# ===

# global logging config
logging.basicConfig(
    level=logging.WARNING, format="%(name)s\t%(levelname)s\t%(message)s"
)

# specific module config
# logging.getLogger("cognition.language").setLevel(logging.INFO)
