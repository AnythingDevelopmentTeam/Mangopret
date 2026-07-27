import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gui"))


def pytest_configure(config):
    from core.platform import PlatformInfo
    PlatformInfo.is_windows = sys.platform == "win32"
    PlatformInfo.is_linux = sys.platform == "linux"


def pytest_runtest_teardown(item):
    from core.platform import PlatformInfo
    PlatformInfo.is_windows = sys.platform == "win32"
    PlatformInfo.is_linux = sys.platform == "linux"
