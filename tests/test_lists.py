import tempfile
from pathlib import Path
from core.lists import ListManager


class TestListManager:
    def setup_method(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="mangopret_test_"))
        self.utils_dir = self.tmpdir / "utils"
        self.utils_dir.mkdir()
        self.lm = ListManager(str(self.tmpdir), str(self.utils_dir))

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_ensure_user_lists_creates_files(self) -> None:
        assert (self.tmpdir / "ipset-exclude-user.txt").exists()
        assert (self.tmpdir / "list-general-user.txt").exists()
        assert (self.tmpdir / "list-exclude-user.txt").exists()

    def test_get_list_files_empty(self) -> None:
        files = self.lm.get_list_files()
        assert len(files) >= 3

    def test_write_and_read_list(self) -> None:
        self.lm.write_list("test-list.txt", "line1\nline2")
        content = self.lm.read_list("test-list.txt")
        assert "line1" in content
        assert "line2" in content

    def test_write_list_adds_newline(self) -> None:
        self.lm.write_list("test.txt", "no newline")
        content = self.lm.read_list("test.txt")
        assert content.endswith("\n")

    def test_read_nonexistent_returns_empty(self) -> None:
        content = self.lm.read_list("nonexistent.txt")
        assert content == ""

    def test_add_entry(self) -> None:
        self.lm.add_entry("test.txt", "new.domain.com")
        content = self.lm.read_list("test.txt")
        assert "new.domain.com" in content

    def test_add_entry_duplicate_ignored(self) -> None:
        self.lm.add_entry("test.txt", "domain.com")
        self.lm.add_entry("test.txt", "domain.com")
        content = self.lm.read_list("test.txt")
        assert content.count("domain.com") == 1

    def test_remove_entry(self) -> None:
        self.lm.write_list("test.txt", "keep\nremove\nkeep2")
        self.lm.remove_entry("test.txt", "remove")
        content = self.lm.read_list("test.txt")
        assert "remove" not in content
        assert "keep" in content

    def test_get_domain_list_files(self) -> None:
        self.lm.write_list("list-test.txt", "content")
        domain_files = self.lm.get_domain_list_files()
        assert "list-test.txt" in domain_files

    def test_get_ipset_list_files(self) -> None:
        self.lm.write_list("ipset-test.txt", "content")
        ipset_files = self.lm.get_ipset_list_files()
        assert "ipset-test.txt" in ipset_files
