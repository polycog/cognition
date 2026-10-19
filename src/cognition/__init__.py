"""
Polycog cognition library
"""

import logging
import os

from .cogent import *
from .decision import *
from .knowledge import *
from .language import *
from .reasoning import *
from .util import *

# ===

logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)
logger.addHandler(logging.NullHandler())

if "PYDANTIC_AI_NO_BANNER" not in os.environ:
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"

# ===

__version__ = "1.0.3"
