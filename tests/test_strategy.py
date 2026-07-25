import tempfile
from pathlib import Path
from core.strategy import Strategy, StrategyRule, StrategyParser


SAMPLE_STRATEGY_JSON = """{
  "id": "test_strategy",
  "name": "Test Strategy",
  "description": "A test strategy",
  "version": "1.0",
  "author": "test",
  "wf_tcp": "80,443",
  "wf_udp": "443",
  "rules": [
    {
      "name": "Rule 1",
      "filter-tcp": "443",
      "dpi-desync": "fake",
      "dpi-desync-repeats": "6",
      "dpi-desync-fooling": "ts"
    }
  ]
}"""


class TestStrategyRule:
    def test_to_args_simple(self) -> None:
        rule = StrategyRule(name="test", params={"filter-tcp": "443", "dpi-desync": "fake"})
        args = rule.to_args()
        assert "--filter-tcp=443" in args
        assert "--dpi-desync=fake" in args

    def test_to_args_list_value(self) -> None:
        rule = StrategyRule(name="test", params={"hostlist": ["list1.txt", "list2.txt"]})
        args = rule.to_args()
        assert "--hostlist" in args
        assert args.count("--hostlist") == 2

    def test_to_args_bool_true(self) -> None:
        rule = StrategyRule(name="test", params={"some-flag": True})
        args = rule.to_args()
        assert "--some-flag" in args

    def test_to_args_bool_false_excluded(self) -> None:
        rule = StrategyRule(name="test", params={"some-flag": False})
        args = rule.to_args()
        assert "--some-flag" not in args

    def test_to_args_none_excluded(self) -> None:
        rule = StrategyRule(name="test", params={"some-flag": None})
        args = rule.to_args()
        assert "--some-flag" not in args


class TestStrategy:
    def test_to_dict(self) -> None:
        s = Strategy(id="test", name="Test", description="desc")
        s.rules = [StrategyRule(name="r1", params={"k": "v"})]
        d = s.to_dict()
        assert d["id"] == "test"
        assert d["name"] == "Test"
        assert len(d["rules"]) == 1
        assert d["rules"][0]["name"] == "r1"

    def test_build_command_windows(self) -> None:
        s = Strategy(id="test", name="Test")
        s.wf_tcp = "80,443"
        s.wf_udp = "443"
        s.rules = [
            StrategyRule(name="r1", params={"filter-tcp": "443", "dpi-desync": "fake"})
        ]
        cmd = s.build_command("winws.exe", "C:\\bin", "C:\\lists", is_windows=True)
        assert cmd[0] == "winws.exe"
        assert "--wf-tcp=80,443" in cmd
        assert "--wf-udp=443" in cmd
        assert "--filter-tcp" in cmd

    def test_build_command_linux(self) -> None:
        s = Strategy(id="test", name="Test")
        s.rules = [
            StrategyRule(name="r1", params={"filter-tcp": "443", "dpi-desync": "fake"})
        ]
        cmd = s.build_command("/opt/zapret/nfq/nfqws", "/bin", "/lists", is_windows=False)
        assert cmd[0] == "/opt/zapret/nfq/nfqws"
        assert "--wf-tcp" not in cmd

    def test_resolve_path_placeholders(self) -> None:
        result = Strategy._resolve_path("{bin}/test.bin", "/mybin", "/mylists")
        assert "/mybin/" in result
        assert "test.bin" in result

        result = Strategy._resolve_path("{lists}/list.txt", "/mybin", "/mylists")
        assert "/mylists/" in result


class TestStrategyParser:
    def test_from_json_valid(self) -> None:
        path = Path(tempfile.mktemp(suffix=".strategy"))
        path.write_text(SAMPLE_STRATEGY_JSON, encoding="utf-8")
        s = StrategyParser.from_file(str(path))
        assert s is not None
        assert s.id == "test_strategy"
        assert s.name == "Test Strategy"
        assert len(s.rules) == 1
        path.unlink()

    def test_from_json_invalid(self) -> None:
        path = Path(tempfile.mktemp(suffix=".strategy"))
        path.write_text("not json", encoding="utf-8")
        s = StrategyParser.from_file(str(path))
        assert s is None
        path.unlink()

    def test_from_json_empty_rules(self) -> None:
        path = Path(tempfile.mktemp(suffix=".strategy"))
        path.write_text('{"id": "empty", "name": "Empty", "rules": []}', encoding="utf-8")
        s = StrategyParser.from_file(str(path))
        assert s is not None
        assert len(s.rules) == 0
        path.unlink()

    def test_from_file_unknown_extension(self) -> None:
        path = Path(tempfile.mktemp(suffix=".txt"))
        path.write_text("content", encoding="utf-8")
        s = StrategyParser.from_file(str(path))
        assert s is None
        path.unlink()

    def test_strategy_to_strategy_file_roundtrip(self) -> None:
        s = Strategy(id="roundtrip", name="Roundtrip", description="test")
        s.rules = [StrategyRule(name="r1", params={"k": "v"})]

        out = Path(tempfile.mktemp(suffix=".strategy"))
        StrategyParser.to_strategy_file(s, str(out))

        loaded = StrategyParser.from_file(str(out))
        assert loaded is not None
        assert loaded.id == "roundtrip"
        assert loaded.name == "Roundtrip"
        assert len(loaded.rules) == 1
        out.unlink()
