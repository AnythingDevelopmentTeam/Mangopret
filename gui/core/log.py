import logging
import sys
from pathlib import Path

_LOG: logging.Logger | None = None
_LOG_DIR: Path | None = None


def set_log_dir(log_dir: str) -> None:
    global _LOG_DIR
    _LOG_DIR = Path(log_dir)
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    if _LOG is not None:
        _add_file_handler(_LOG)


def _add_file_handler(logger: logging.Logger) -> None:
    if _LOG_DIR is None:
        return
    log_file = _LOG_DIR / "mangopret.log"
    fh = logging.FileHandler(str(log_file), encoding="utf-8", mode="a")
    fh.setFormatter(
        logging.Formatter(fmt="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    )
    logger.addHandler(fh)


def get_logger(name: str = "mangopret") -> logging.Logger:
    global _LOG
    if _LOG is None:
        _LOG = logging.getLogger(name)
        _LOG.setLevel(logging.INFO)

        fmt = logging.Formatter(fmt="[%(name)s] %(levelname)s %(message)s")
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(fmt)
        _LOG.addHandler(h)

        if _LOG_DIR is not None:
            _add_file_handler(_LOG)
    return _LOG
