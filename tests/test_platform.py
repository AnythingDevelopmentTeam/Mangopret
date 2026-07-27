import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from core.platform import PlatformInfo


SAMPLE_STRATEGY_RULE = MagicMock()
SAMPLE_STRATEGY_RULE.params = {}
SAMPLE_STRATEGY_RULE.to_args.return_value = []

SAMPLE_STRATEGY = MagicMock()
SAMPLE_STRATEGY.rules = [SAMPLE_STRATEGY_RULE]
SAMPLE_STRATEGY.wf_tcp = "80,443"
SAMPLE_STRATEGY.wf_udp = "443"


class TestPlatformInfoInit:
    def _linux_platform(self):
        PlatformInfo.is_windows = False
        PlatformInfo.is_linux = True

    def _windows_platform(self):
        PlatformInfo.is_windows = True
        PlatformInfo.is_linux = False

    def setup_method(self):
        self._windows_platform()

    def test_linux_defaults(self):
        self._linux_platform()
        p = PlatformInfo("/tmp/test_base")
        assert p.is_windows is False
        assert p.is_linux is True
        assert p.base_dir == Path("/tmp/test_base")

    def test_windows_defaults(self):
        p = PlatformInfo("C:\\test_base")
        assert p.is_windows is True
        assert p.is_linux is False
        assert p.binary == Path("C:\\test_base\\bin\\winws.exe")

    def test_binary_resolution_linux_found(self):
        self._linux_platform()
        with patch("pathlib.Path.exists", return_value=True):
            p = PlatformInfo("/tmp/test_base")
            assert "nfqws" in str(p.binary)

    def test_binary_resolution_linux_not_found_fallsback(self):
        self._linux_platform()
        with patch("pathlib.Path.exists", return_value=False):
            p = PlatformInfo("/tmp/test_base")
            assert "nfqws" in str(p.binary)
            assert "opt" in str(p.binary)

    def test_config_dir_linux(self):
        self._linux_platform()
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            with patch.dict("os.environ", {"APPDATA": ""}, clear=False):
                p = PlatformInfo("/tmp/base")
                assert "mangopret" in str(p.config_dir)
                assert ".config" in str(p.config_dir)

    def test_config_dir_windows(self):
        with patch.dict("os.environ", {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"}):
            p = PlatformInfo("C:\\base")
            assert "mangopret" in str(p.config_dir)
            assert "Roaming" in str(p.config_dir)


class TestPlatformInfoBinary:
    def test_is_binary_present_true(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = PlatformInfo("/tmp/base")
            assert p.is_binary_present() is True

    def test_is_binary_present_false(self):
        with patch("pathlib.Path.exists", return_value=False):
            p = PlatformInfo("/tmp/base")
            assert p.is_binary_present() is False

    def test_is_zapret_installed_linux_true(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = PlatformInfo("/tmp/base")
            p.is_windows = False
            p.is_linux = True
            assert p.is_zapret_installed() is True

    def test_is_zapret_installed_linux_false(self):
        with patch("pathlib.Path.exists", return_value=False):
            p = PlatformInfo("/tmp/base")
            p.is_windows = False
            p.is_linux = True
            assert p.is_zapret_installed() is False

    def test_is_zapret_installed_windows(self):
        with patch("core.platform.sys.platform", "win32"):
            p = PlatformInfo("C:\\base")
            assert p.is_zapret_installed() is True


class TestPlatformInfoProcess:
    def _make_linux(self, p):
        p.is_windows = False
        p.is_linux = True
        return p

    def test_start_process_returns_popen(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            with patch("subprocess.Popen") as mock_popen:
                proc = p.start_process(["--test"])
                assert proc is not None
                mock_popen.assert_called_once()

    def test_start_process_failure_returns_none(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            with patch("subprocess.Popen", side_effect=Exception("fail")):
                proc = p.start_process(["--test"])
                assert proc is None

    def test_stop_process_terminates(self):
        mock_proc = MagicMock()
        p = self._make_linux(PlatformInfo("/tmp/base"))
        p.stop_process(mock_proc)
        mock_proc.terminate.assert_called_once()

    def test_stop_process_none_noop(self):
        with patch("core.platform.sys.platform", "linux"):
            p = PlatformInfo("/tmp/base")
            p.stop_process(None)

    def test_is_process_running_windows_true(self):
        with patch("core.platform.sys.platform", "win32"):
            p = PlatformInfo("C:\\base")
            mock_run = MagicMock()
            mock_run.stdout = "winws.exe"
            mock_run.returncode = 0
            with patch("subprocess.run", return_value=mock_run):
                assert p.is_process_running() is True

    def test_is_process_running_windows_false(self):
        with patch("core.platform.sys.platform", "win32"):
            p = PlatformInfo("C:\\base")
            mock_run = MagicMock()
            mock_run.stdout = ""
            with patch("subprocess.run", return_value=mock_run):
                assert p.is_process_running() is False

    def test_is_process_running_linux_true(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            mock_run = MagicMock()
            mock_run.returncode = 0
            with patch("subprocess.run", return_value=mock_run):
                assert p.is_process_running("nfqws") is True

    def test_is_process_running_linux_false(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            mock_run = MagicMock()
            mock_run.returncode = 1
            with patch("subprocess.run", return_value=mock_run):
                assert p.is_process_running("nfqws") is False

    def test_kill_all_calls_taskkill_windows(self):
        with patch("core.platform.sys.platform", "win32"):
            p = PlatformInfo("C:\\base")
            with patch("subprocess.run") as mock_run:
                p.kill_all()
                mock_run.assert_called_once()
                args = mock_run.call_args[0][0]
                assert "taskkill" in args

    def test_kill_all_calls_pkill_linux(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            with patch("subprocess.run") as mock_run:
                p.kill_all()
                mock_run.assert_called_once()
                args = mock_run.call_args[0][0]
                assert "pkill" in args


class TestPlatformInfoService:
    def _make_linux(self, p):
        p.is_windows = False
        p.is_linux = True
        return p

    def test_get_service_status_windows_running(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.stdout = "RUNNING"
        with patch("subprocess.run", return_value=mock_run):
            assert p.get_service_status() == "running"

    def test_get_service_status_windows_stopped(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.stdout = "STOPPED"
        with patch("subprocess.run", return_value=mock_run):
            assert p.get_service_status() == "stopped"

    def test_get_service_status_windows_not_installed(self):
        p = PlatformInfo("C:\\base")
        with patch("subprocess.run", side_effect=Exception):
            assert p.get_service_status() == "not_installed"

    def test_get_service_status_linux_not_installed(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        with patch.object(Path, "exists", return_value=False):
            assert p.get_service_status() == "not_installed"

    def test_get_service_status_linux_running(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        mock_run = MagicMock()
        mock_run.stdout = "active\n"
        with patch.object(Path, "exists", return_value=True):
            with patch("subprocess.run", return_value=mock_run):
                assert p.get_service_status() == "running"

    def test_is_service_enabled_linux_true(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        mock_run = MagicMock()
        mock_run.stdout = "enabled"
        with patch("subprocess.run", return_value=mock_run):
            assert p.is_service_enabled() is True

    def test_is_service_enabled_linux_false(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        mock_run = MagicMock()
        mock_run.stdout = "disabled"
        with patch("subprocess.run", return_value=mock_run):
            assert p.is_service_enabled() is False

    def test_service_start_linux(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            mock_run = MagicMock()
            mock_run.returncode = 0
            with patch("subprocess.run", return_value=mock_run):
                ok, _ = p.service_start()
                assert ok is True

    def test_service_start_windows(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.returncode = 0
        with patch("subprocess.run", return_value=mock_run):
            ok, _ = p.service_start()
            assert ok is True

    def test_service_install_linux(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            with patch.object(p, "create_systemd_service", return_value=True):
                ok, _ = p.service_install(SAMPLE_STRATEGY, "test")
                assert ok is True

    def test_service_install_windows(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.returncode = 0
        with patch("subprocess.run", return_value=mock_run):
            ok, _ = p.service_install(SAMPLE_STRATEGY, "test")
            assert ok is True

    def test_service_remove_linux(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            mock_run = MagicMock()
            mock_run.returncode = 0
            with patch("subprocess.run", return_value=mock_run):
                with patch.object(Path, "exists", return_value=False):
                    ok, _ = p.service_remove()
                    assert ok is True

    def test_service_remove_windows(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.returncode = 0
        with patch("subprocess.run", return_value=mock_run):
            ok, _ = p.service_remove()
            assert ok is True


class TestPlatformInfoCreateSystemdService:
    def _make_linux(self, p):
        p.is_windows = False
        p.is_linux = True
        return p

    @patch("core.platform.Path.exists", return_value=True)
    @patch("core.platform.Path.read_text", return_value="")
    @patch("core.platform.Path.write_text")
    @patch("subprocess.run")
    def test_creates_service(self, mock_run, mock_write, mock_read, mock_exists):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            with patch.object(p, "_sync_ipset_files"):
                with patch.object(p, "_install_zapret_service_unit"):
                    result = p.create_systemd_service(SAMPLE_STRATEGY, "test")
                    assert result is True
                    mock_write.assert_called_once()

    def test_returns_false_on_any_exception(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            with patch.object(Path, "read_text", side_effect=Exception("boom")):
                result = p.create_systemd_service(SAMPLE_STRATEGY, "test")
                assert result is False


class TestPlatformInfoStartup:
    def _make_linux(self, p):
        p.is_windows = False
        p.is_linux = True
        return p

    def test_is_startup_enabled_windows_found(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.returncode = 0
        with patch("subprocess.run", return_value=mock_run):
            assert p.is_startup_enabled() is True

    def test_is_startup_enabled_windows_not_found(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.returncode = 1
        with patch("subprocess.run", return_value=mock_run):
            assert p.is_startup_enabled() is False

    def test_is_startup_enabled_linux_true(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        with patch("pathlib.Path.exists", return_value=True):
            assert p.is_startup_enabled() is True

    def test_is_startup_enabled_linux_false(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        with patch("pathlib.Path.exists", return_value=False):
            assert p.is_startup_enabled() is False

    def test_enable_startup_linux(self):
        PlatformInfo.is_windows = False
        PlatformInfo.is_linux = True
        p = PlatformInfo("/tmp/base")
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            with patch("pathlib.Path.mkdir"):
                with patch("pathlib.Path.write_text"):
                    with patch.object(Path, "chmod"):
                        ok, _ = p.enable_startup()
                        assert ok is True

    def test_enable_startup_windows(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.returncode = 0
        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.run", return_value=mock_run):
                ok, _ = p.enable_startup()
                assert ok is True

    def test_disable_startup_linux(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.unlink"):
                    ok, _ = p.disable_startup()
                    assert ok is True

    def test_disable_startup_windows(self):
        p = PlatformInfo("C:\\base")
        mock_run = MagicMock()
        mock_run.returncode = 0
        with patch("subprocess.run", return_value=mock_run):
            ok, _ = p.disable_startup()
            assert ok is True


class TestPlatformInfoDesktopEntry:
    def _make_linux(self, p):
        p.is_windows = False
        p.is_linux = True
        return p

    def test_create_desktop_entry_non_linux(self):
        p = PlatformInfo("C:\\base")
        ok, msg = p.create_desktop_entry()
        assert ok is False
        assert "Not Linux" in msg

    def test_create_desktop_entry_linux_success(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            with patch("pathlib.Path.mkdir"):
                with patch.object(Path, "read_text", return_value="Exec=run_gui.sh"):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "write_text"):
                            with patch.object(Path, "chmod"):
                                ok, _ = p.create_desktop_entry()
                                assert ok is True

    def test_remove_desktop_entry_linux_success(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "unlink"):
                    ok, _ = p.remove_desktop_entry()
                    assert ok is True

    def test_is_desktop_entry_installed_linux_true(self):
        p = self._make_linux(PlatformInfo("/tmp/base"))
        with patch("pathlib.Path.home", return_value=Path("/home/user")):
            with patch("pathlib.Path.exists", return_value=True):
                assert p.is_desktop_entry_installed() is True

    def test_is_desktop_entry_installed_non_linux(self):
        p = PlatformInfo("C:\\base")
        assert p.is_desktop_entry_installed() is False


class TestPlatformInfoGetConfigValue:
    def test_returns_default_when_no_config(self):
        with patch("pathlib.Path.exists", return_value=False):
            p = PlatformInfo("/tmp/base")
            val = p._get_config_value("nfqueue_num", "200")
            assert val == "200"

    def test_returns_value_when_config_exists(self):
        mock_json = '{"nfqueue_num": "300"}'
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = mock_json
            mock_open.return_value = mock_file
            with patch("pathlib.Path.exists", return_value=True):
                p = PlatformInfo("/tmp/base")
                val = p._get_config_value("nfqueue_num", "200")
                assert val == "300"


class TestPlatformInfoJournal:
    def _make_linux(self, p):
        p.is_windows = False
        p.is_linux = True
        return p

    def test_get_journal_logs_linux(self):
        with patch("pathlib.Path.exists", return_value=True):
            p = self._make_linux(PlatformInfo("/tmp/base"))
            mock_run = MagicMock()
            mock_run.stdout = "log line 1\nlog line 2"
            with patch("subprocess.run", return_value=mock_run):
                logs = p.get_journal_logs(2)
                assert "log line" in logs

    def test_get_journal_logs_windows_empty(self):
        p = PlatformInfo("C:\\base")
        assert p.get_journal_logs() == ""
