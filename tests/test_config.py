import json
import tempfile
from pathlib import Path
from core.config import Config


class TestConfig:
    def setup_method(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="mangopret_test_"))
        self.config = Config(str(self.tmpdir))

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_defaults(self) -> None:
        assert self.config.get("ipset_mode") == "loaded"
        assert self.config.get("theme") == "system"
        assert self.config.get("nfqueue_num") == "200"

    def test_set_and_get(self) -> None:
        self.config.set("theme", "dark")
        assert self.config.get("theme") == "dark"

    def test_setitem_getitem(self) -> None:
        self.config["last_strategy"] = "general (EXP)"
        assert self.config["last_strategy"] == "general (EXP)"

    def test_persistence(self) -> None:
        self.config.set("theme", "dark")
        config2 = Config(str(self.tmpdir))
        assert config2.get("theme") == "dark"

    def test_config_file_created(self) -> None:
        self.config.set("test_key", "test_value")
        assert self.config.config_file.exists()
        with open(self.config.config_file, "r") as f:
            data = json.load(f)
        assert data["test_key"] == "test_value"

    def test_unknown_key_returns_default(self) -> None:
        assert self.config.get("nonexistent", "fallback") == "fallback"

    def test_corrupted_config_falls_back_to_defaults(self) -> None:
        self.config.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config.config_file.write_text("invalid json", encoding="utf-8")
        c = Config(str(self.tmpdir))
        assert c.get("ipset_mode") == "loaded"

    def _big_ipset(self, entries: list[str]) -> str:
        return "\n".join(entries * 10) + "\n"

    def test_ipset_mode_none(self) -> None:
        lists_dir = self.tmpdir / "lists"
        lists_dir.mkdir()
        ipset_file = lists_dir / "ipset-all.txt"
        ipset_file.write_text(self._big_ipset(["1.2.3.4/32"]), encoding="utf-8")

        self.config.set_ipset_mode("none", str(lists_dir))
        content = ipset_file.read_text(encoding="utf-8")
        assert "203.0.113.113" in content

    def test_ipset_mode_loaded(self) -> None:
        lists_dir = self.tmpdir / "lists"
        lists_dir.mkdir()
        ipset_file = lists_dir / "ipset-all.txt"
        ipset_file.write_text(self._big_ipset(["1.2.3.4/32"]), encoding="utf-8")
        backup_file = lists_dir / "ipset-all.txt.backup"
        backup_file.write_text(self._big_ipset(["5.6.7.8/32"]), encoding="utf-8")

        self.config.set_ipset_mode("loaded", str(lists_dir))
        content = ipset_file.read_text(encoding="utf-8")
        assert "5.6.7.8" in content
