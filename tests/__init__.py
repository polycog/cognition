"""
Testing config
"""

# import logging
import pickle

# ===

# handler = logging.StreamHandler()
# handler.setFormatter(
#     logging.Formatter("%(levelname)s\t%(name)s\t%(asctime)s\t%(message)s")
# )

# logger = logging.getLogger("cognition.cogent")
# logger.setLevel(logging.INFO)
# logger.addHandler(handler)

# ===


def _test_pickle(o: object) -> None:
    """Confirms pickle/depickle"""

    serialized = pickle.dumps(o)
    _ = pickle.loads(serialized)
