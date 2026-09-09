"""
Polycog cognition library
"""

import logging

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

# ===

__version__ = "1.0.0"
