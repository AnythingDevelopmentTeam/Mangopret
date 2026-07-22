import os
import json
from pathlib import Path
from typing import Optional


class Config:
    _defaults = {
        "game_filter": "disabled",
        "game_filter_tcp": "12",
        "game_filter_udp": "12",
        "ipset_mode": "loaded",
        "check_updates": True,
        "last_strategy": "",
        "minimize_to_tray": True,
        "auto_start": False,
        "theme": "dark",
        "nfqueue_num": "200",
        "linux_zapret_path": "",
    }

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self._data = dict(self._defaults)
        self.load()

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except Exception:
                pass

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def __getitem__(self, key):
        return self._data.get(key)

    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()

    @property
    def game_filter_tcp(self) -> str:
        mode = self._data.get("game_filter", "disabled")
        if mode == "all":
            return "1024-65535"
        elif mode == "tcp":
            return "1024-65535"
        return "12"

    @property
    def game_filter_udp(self) -> str:
        mode = self._data.get("game_filter", "disabled")
        if mode == "all":
            return "1024-65535"
        elif mode == "udp":
            return "1024-65535"
        return "12"

    def set_game_filter(self, mode: str):
        self._data["game_filter"] = mode
        self.save()

    def get_ipset_mode(self, lists_dir: str) -> str:
        ipset_file = Path(lists_dir) / "ipset-all.txt"
        if not ipset_file.exists():
            return "none"
        try:
            size = ipset_file.stat().st_size
            if size < 100:
                content = ipset_file.read_text(encoding="utf-8").strip()
                if "203.0.113.113" in content:
                    return "none"
                if content == "":
                    return "any"
            return "loaded"
        except Exception:
            return "none"

    def set_ipset_mode(self, mode: str, lists_dir: str):
        ipset_file = Path(lists_dir) / "ipset-all.txt"
        backup_file = Path(lists_dir) / "ipset-all.txt.backup"

        if mode == "none":
            if ipset_file.exists() and ipset_file.stat().st_size > 100:
                content = ipset_file.read_text(encoding="utf-8")
                if "203.0.113.113" not in content:
                    if backup_file.exists():
                        backup_file.unlink()
                    ipset_file.rename(backup_file)
            ipset_file.write_text("203.0.113.113/32\n", encoding="utf-8")
        elif mode == "any":
            if ipset_file.exists() and ipset_file.stat().st_size > 100:
                content = ipset_file.read_text(encoding="utf-8")
                if "203.0.113.113" not in content:
                    if backup_file.exists():
                        backup_file.unlink()
                    ipset_file.rename(backup_file)
            ipset_file.write_text("", encoding="utf-8")
        elif mode == "loaded":
            if backup_file.exists() and backup_file.stat().st_size > 100:
                if ipset_file.exists():
                    ipset_file.unlink()
                backup_file.rename(ipset_file)

        self._data["ipset_mode"] = mode
        self.save()
