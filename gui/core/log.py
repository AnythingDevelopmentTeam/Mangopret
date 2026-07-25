import logging
import sys

_LOG: logging.Logger | None = None


def get_logger(name: str = "mangopret") -> logging.Logger:
    global _LOG
    if _LOG is None:
        fmt = logging.Formatter(fmt="[%(name)s] %(levelname)s %(message)s")
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(fmt)
        _LOG = logging.getLogger(name)
        _LOG.addHandler(h)
        _LOG.setLevel(logging.INFO)
    return _LOG
