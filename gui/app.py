import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import glob
import threading
import time
import sys
import ctypes

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

ZAPRET_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(ZAPRET_DIR, "bin")
LISTS_DIR = os.path.join(ZAPRET_DIR, "lists")
SERVICE_BAT = os.path.join(ZAPRET_DIR, "service.bat")
AUTORUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "ZapretGUI"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def request_admin():
    if is_admin():
        return True
    script = os.path.abspath(__file__)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}"', None, 1
    )
    sys.exit(0)


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=timeout, cwd=ZAPRET_DIR
        )
        out = r.stdout.decode("utf-8", errors="replace")
        err = r.stderr.decode("utf-8", errors="replace")
        return out + err
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return str(e)


def get_strategies():
    strategies = []
    for f in sorted(glob.glob(os.path.join(ZAPRET_DIR, "general*.bat"))):
        name = os.path.splitext(os.path.basename(f))[0]
        strategies.append((name, f))
    return strategies


def get_service_status():
    out = run_cmd("sc query zapret", timeout=10)
    if "RUNNING" in out:
        return "running"
    elif "STOPPED" in out:
        return "stopped"
    return "not_installed"


def get_game_filter_status():
    gf_file = os.path.join(ZAPRET_DIR, "utils", "game_filter.enabled")
    if os.path.exists(gf_file):
        with open(gf_file, "r") as f:
            val = f.read().strip()
        return val if val else "disabled"
    return "disabled"


def get_ipset_status():
    ipset = os.path.join(LISTS_DIR, "ipset-all.txt")
    if not os.path.exists(ipset):
        return "none"
    with open(ipset, "r") as f:
        content = f.read().strip()
    if "203.0.113.113" in content:
        return "none"
    if content == "":
        return "any"
    return "loaded"


def is_winws_running():
    out = run_cmd('tasklist /FI "IMAGENAME eq winws.exe"', timeout=5)
    return "winws.exe" in out


def create_tray_icon(color="green"):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colors = {"green": "#4CAF50", "red": "#F44336", "gray": "#9E9E9E"}
    c = colors.get(color, "#9E9E9E")
    draw.rectangle([8, 8, 56, 56], fill=c, outline="white", width=3)
    draw.text((18, 18), "Z", fill="white")
    return img


class ZapretGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zapret GUI Manager")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self.process = None
        self.strategies = get_strategies()
        self.strategy_names = [s[0] for s in self.strategies]
        self.active_strategy = None
        self.tray_icon = None
        self._hidden = False

        self._build_ui()
        self._refresh_status()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        if HAS_TRAY:
            self._start_tray()

    def _start_tray(self):
        self.tray_icon = pystray.Icon(
            APP_NAME,
            create_tray_icon("green"),
            "Zapret GUI",
            menu=self._build_tray_menu()
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _build_tray_menu(self):
        items = [
            pystray.MenuItem("Show", self._tray_show, default=True),
            pystray.MenuItem(lambda item: f"Status: {'RUNNING' if is_winws_running() else 'STOPPED'}", None, enabled=False),
            pystray.MenuItem(lambda item: f"Strategy: {self.active_strategy or 'none'}", None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]

        strategy_items = []
        for name in self.strategy_names:
            strategy_items.append(
                pystray.MenuItem(name, self._tray_start_strategy)
            )

        items.append(pystray.MenuItem("Strategies", pystray.Menu(*strategy_items)))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Start", self._tray_start_current))
        items.append(pystray.MenuItem("Stop", self._tray_stop))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Autorun", self._tray_toggle_autorun, checked=self._is_autorun))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Exit", self._tray_exit))

        return pystray.Menu(*items)

    def _tray_show(self, icon=None, item=None):
        self.root.after(0, self._show_window)

    def _show_window(self):
        self._hidden = False
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _tray_start_strategy(self, icon=None, item=None):
        name = str(item) if item else None
        if not name:
            return
        self.root.after(0, lambda: self._do_start(name))

    def _tray_start_current(self, icon=None, item=None):
        self.root.after(0, self._start_strategy)

    def _tray_stop(self, icon=None, item=None):
        self.root.after(0, self._stop_strategy)

    def _tray_exit(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def _is_autorun(self, item=None):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTORUN_KEY, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _tray_toggle_autorun(self, icon=None, item=None):
        self.root.after(0, self._toggle_autorun)

    def _toggle_autorun(self):
        try:
            import winreg
            exe = sys.executable
            script = os.path.abspath(__file__)
            cmd = f'"{exe}" "{script}"'

            if self._is_autorun():
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTORUN_KEY, 0, winreg.KEY_SET_ACCESS)
                winreg.DeleteValue(key, APP_NAME)
                winreg.CloseKey(key)
                self._log("Autorun DISABLED")
            else:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTORUN_KEY, 0, winreg.KEY_SET_ACCESS)
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                winreg.CloseKey(key)
                self._log("Autorun ENABLED")
        except Exception as e:
            self._log(f"Autorun error: {e}")

    def _on_close(self):
        if HAS_TRAY:
            self._hidden = True
            self.root.withdraw()
        else:
            self._tray_exit()

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Green.TLabel", foreground="green", font=("Segoe UI", 10, "bold"))
        style.configure("Red.TLabel", foreground="red", font=("Segoe UI", 10, "bold"))
        style.configure("Admin.TLabel", foreground="#FF6600", font=("Segoe UI", 9, "bold"))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_main = ttk.Frame(notebook)
        tab_lists = ttk.Frame(notebook)
        tab_service = ttk.Frame(notebook)
        tab_log = ttk.Frame(notebook)

        notebook.add(tab_main, text="  Main  ")
        notebook.add(tab_lists, text="  Lists  ")
        # notebook.add(tab_service, text="  Service  ")  # TODO: coming soon
        notebook.add(tab_log, text="  Log  ")

        # Service tab coming soon
        coming_soon = ttk.Label(self.root, text="Service tab coming soon", foreground="gray", font=("Segoe UI", 9, "italic"))
        coming_soon.pack(side=tk.BOTTOM, pady=5)

        self._build_main_tab(tab_main)
        self._build_lists_tab(tab_lists)
        self._build_log_tab(tab_log)

    def _build_main_tab(self, parent):
        frame = ttk.LabelFrame(parent, text="Strategy", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=10)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Select strategy:").pack(side=tk.LEFT)
        self.strategy_var = tk.StringVar(value=self.strategy_names[0] if self.strategy_names else "")
        self.strategy_combo = ttk.Combobox(
            row, textvariable=self.strategy_var, values=self.strategy_names, state="readonly", width=40
        )
        self.strategy_combo.pack(side=tk.LEFT, padx=(10, 0))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        self.btn_start = ttk.Button(btn_frame, text="Start", command=self._start_strategy, width=15)
        self.btn_start.pack(side=tk.LEFT)
        self.btn_stop = ttk.Button(btn_frame, text="Stop", command=self._stop_strategy, width=15, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=(10, 0))

        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        row_admin = ttk.Frame(status_frame)
        row_admin.pack(fill=tk.X)
        ttk.Label(row_admin, text="Admin:").pack(side=tk.LEFT)
        admin_text = "YES" if is_admin() else "NO"
        self.lbl_admin = ttk.Label(row_admin, text=admin_text, style="Green.TLabel" if is_admin() else "Red.TLabel")
        self.lbl_admin.pack(side=tk.LEFT, padx=(10, 0))

        row2 = ttk.Frame(status_frame)
        row2.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(row2, text="Service:").pack(side=tk.LEFT)
        self.lbl_service = ttk.Label(row2, text="checking...", style="Status.TLabel")
        self.lbl_service.pack(side=tk.LEFT, padx=(10, 0))

        row3 = ttk.Frame(status_frame)
        row3.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(row3, text="Game Filter:").pack(side=tk.LEFT)
        self.lbl_game = ttk.Label(row3, text="checking...", style="Status.TLabel")
        self.lbl_game.pack(side=tk.LEFT, padx=(10, 0))

        row4 = ttk.Frame(status_frame)
        row4.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(row4, text="IPSet Filter:").pack(side=tk.LEFT)
        self.lbl_ipset = ttk.Label(row4, text="checking...", style="Status.TLabel")
        self.lbl_ipset.pack(side=tk.LEFT, padx=(10, 0))

        row5 = ttk.Frame(status_frame)
        row5.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(row5, text="winws.exe:").pack(side=tk.LEFT)
        self.lbl_winws = ttk.Label(row5, text="checking...", style="Status.TLabel")
        self.lbl_winws.pack(side=tk.LEFT, padx=(10, 0))

        ctrl_frame = ttk.LabelFrame(parent, text="Quick Controls", padding=10)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        row6 = ttk.Frame(ctrl_frame)
        row6.pack(fill=tk.X)
        ttk.Label(row6, text="Game Filter:").pack(side=tk.LEFT)
        self.game_filter_var = tk.StringVar(value=get_game_filter_status())
        for val in ["disabled", "all", "tcp", "udp"]:
            ttk.Radiobutton(row6, text=val, variable=self.game_filter_var, value=val, command=self._set_game_filter).pack(side=tk.LEFT, padx=5)

        row7 = ttk.Frame(ctrl_frame)
        row7.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(row7, text="IPSet Filter:").pack(side=tk.LEFT)
        self.ipset_var = tk.StringVar(value=get_ipset_status())
        for val in ["none", "loaded", "any"]:
            ttk.Radiobutton(row7, text=val, variable=self.ipset_var, value=val, command=self._set_ipset_filter).pack(side=tk.LEFT, padx=5)

        row8 = ttk.Frame(ctrl_frame)
        row8.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(row8, text="Refresh Status", command=self._refresh_status, width=18).pack(side=tk.LEFT)
        ttk.Button(row8, text="Run Diagnostics", command=self._run_diagnostics, width=18).pack(side=tk.LEFT, padx=(10, 0))

    def _build_lists_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        ttk.Label(left, text="Domain Lists").pack(anchor=tk.W)
        self.domain_listbox = tk.Listbox(left, font=("Consolas", 10))
        self.domain_listbox.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        for f in ["list-general.txt", "list-general-user.txt", "list-exclude.txt", "list-google.txt"]:
            self.domain_listbox.insert(tk.END, f)
        self.domain_listbox.bind("<<ListboxSelect>>", self._on_domain_select)

        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_row, text="Save", command=self._save_domain_list, width=10).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Add Domain", command=self._add_domain, width=10).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(btn_row, text="Remove Selected", command=self._remove_domain, width=14).pack(side=tk.LEFT, padx=(5, 0))

        self.domain_text = scrolledtext.ScrolledText(right, font=("Consolas", 10), wrap=tk.WORD)
        self.domain_text.pack(fill=tk.BOTH, expand=True)
        self._current_domain_file = None

    def _build_service_tab(self, parent):
        frame = ttk.LabelFrame(parent, text="Windows Service", padding=15)
        frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(frame, text="Manage zapret as a Windows Service (auto-start):").pack(anchor=tk.W)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Install Service", command=self._install_service, width=20).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Remove Services", command=self._remove_services, width=20).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(btn_frame, text="Check Status", command=self._check_service_status, width=20).pack(side=tk.LEFT, padx=(10, 0))

        self.service_log = scrolledtext.ScrolledText(frame, font=("Consolas", 10), height=15, wrap=tk.WORD)
        self.service_log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        svc_menu = tk.Menu(self.service_log, tearoff=0)
        svc_menu.add_command(label="Copy", command=lambda: self.service_log.event_generate("<<Copy>>"))
        svc_menu.add_command(label="Select All", command=lambda: self.service_log.tag_add("sel", "1.0", "end"))
        svc_menu.add_separator()
        svc_menu.add_command(label="Clear", command=lambda: self.service_log.delete("1.0", tk.END))

        def show_svc_menu(event):
            svc_menu.tk_popup(event.x_root, event.y_root)

        self.service_log.bind("<Button-3>", show_svc_menu)

        upd_frame = ttk.LabelFrame(parent, text="Updates", padding=15)
        upd_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        btn_row = ttk.Frame(upd_frame)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="Check for Updates", command=self._check_updates, width=20).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Update IPSet List", command=self._update_ipset, width=20).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(btn_row, text="Update Hosts File", command=self._update_hosts, width=20).pack(side=tk.LEFT, padx=(10, 0))

    def _build_log_tab(self, parent):
        self.log_text = scrolledtext.ScrolledText(parent, font=("Consolas", 10), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        menu = tk.Menu(self.log_text, tearoff=0)
        menu.add_command(label="Copy", command=lambda: self.log_text.event_generate("<<Copy>>"))
        menu.add_command(label="Select All", command=lambda: self.log_text.tag_add("sel", "1.0", "end"))
        menu.add_separator()
        menu.add_command(label="Clear", command=lambda: self.log_text.delete("1.0", tk.END))

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        self.log_text.bind("<Button-3>", show_menu)
        self.log_text.bind("<Control-a>", lambda e: self.log_text.tag_add("sel", "1.0", "end"))
        self.log_text.bind("<Control-c>", lambda e: self.log_text.event_generate("<<Copy>>"))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Copy All", command=self._copy_log_all).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Clear Log", command=lambda: self.log_text.delete("1.0", tk.END)).pack(side=tk.LEFT, padx=(10, 0))

    def _copy_log_all(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get("1.0", tk.END))
        self._log("Log copied to clipboard")

    def _log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)

    def _refresh_status(self):
        svc = get_service_status()
        gf = get_game_filter_status()
        ipset = get_ipset_status()
        winws_running = is_winws_running()

        self.lbl_service.config(text=svc.upper(), style="Green.TLabel" if svc == "running" else "Red.TLabel")
        self.lbl_game.config(text=gf)
        self.lbl_ipset.config(text=ipset)
        self.lbl_winws.config(text="RUNNING" if winws_running else "STOPPED", style="Green.TLabel" if winws_running else "Red.TLabel")

        self.game_filter_var.set(gf)
        self.ipset_var.set(ipset)

        if self.tray_icon:
            color = "green" if winws_running else "red"
            self.tray_icon.icon = create_tray_icon(color)
            status_text = f"Zapret - {'RUNNING' if winws_running else 'STOPPED'}"
            if self.active_strategy:
                status_text += f" ({self.active_strategy})"
            self.tray_icon.title = status_text

    def _start_strategy(self):
        name = self.strategy_var.get()
        if not name:
            messagebox.showwarning("Warning", "Select a strategy first")
            return
        self._do_start(name)

    def _do_start(self, name):
        strategy_path = os.path.join(ZAPRET_DIR, f"{name}.bat")
        if not os.path.exists(strategy_path):
            return

        self._stop_strategy()
        self._log(f"Starting strategy: {name}")
        self.process = subprocess.Popen(
            f'cmd /c "{strategy_path}"', shell=True, cwd=ZAPRET_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        self.active_strategy = name
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self._log(f"Strategy {name} started")
        self.root.after(2000, self._refresh_status)

    def _stop_strategy(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass
            self.process = None

        run_cmd("taskkill /IM winws.exe /F", timeout=10)
        self.active_strategy = None
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self._log("Strategy stopped")
        self.root.after(1000, self._refresh_status)

    def _set_game_filter(self):
        val = self.game_filter_var.get()
        gf_file = os.path.join(ZAPRET_DIR, "utils", "game_filter.enabled")
        os.makedirs(os.path.dirname(gf_file), exist_ok=True)
        with open(gf_file, "w") as f:
            f.write(val)
        self._log(f"Game Filter: {val}")

    def _set_ipset_filter(self):
        val = self.ipset_var.get()
        ipset = os.path.join(LISTS_DIR, "ipset-all.txt")
        backup = os.path.join(LISTS_DIR, "ipset-all.txt.backup")

        if val == "none":
            if os.path.exists(ipset) and os.path.exists(backup) and os.path.getsize(ipset) > 100:
                os.replace(ipset, backup)
            with open(ipset, "w") as f:
                f.write("203.0.113.113/32\n")
        elif val == "any":
            if os.path.exists(ipset) and os.path.getsize(ipset) > 100 and "203.0.113.113" not in open(ipset).read():
                os.replace(ipset, backup)
            with open(ipset, "w") as f:
                f.write("")
        elif val == "loaded":
            if os.path.exists(backup) and os.path.getsize(backup) > 100:
                os.replace(backup, ipset)
        self._log(f"IPSet Filter: {val}")

    def _run_diagnostics(self):
        self._log("Running diagnostics...")
        result = run_cmd(f'"{SERVICE_BAT}" diagnostics', timeout=60)
        self._log(result[:2000] if result else "No output")

    def _on_domain_select(self, event):
        selection = self.domain_listbox.curselection()
        if not selection:
            return
        filename = self.domain_listbox.get(selection[0])
        self._current_domain_file = os.path.join(LISTS_DIR, filename)
        self.domain_text.delete("1.0", tk.END)
        if os.path.exists(self._current_domain_file):
            with open(self._current_domain_file, "r", encoding="utf-8") as f:
                self.domain_text.insert(tk.END, f.read())
        self._log(f"Loaded: {filename}")

    def _save_domain_list(self):
        if not self._current_domain_file:
            messagebox.showwarning("Warning", "Select a list first")
            return
        content = self.domain_text.get("1.0", tk.END).strip()
        with open(self._current_domain_file, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        self._log(f"Saved: {os.path.basename(self._current_domain_file)}")

    def _add_domain(self):
        if not self._current_domain_file:
            messagebox.showwarning("Warning", "Select a list first")
            return
        import tkinter.simpledialog
        domain = tkinter.simpledialog.askstring("Add Domain", "Enter domain:")
        if domain:
            self.domain_text.insert(tk.END, domain.strip() + "\n")
            self._save_domain_list()

    def _remove_domain(self):
        sel = self.domain_text.tag_ranges(tk.SEL)
        if sel:
            self.domain_text.delete(sel[0], sel[1])

    def _install_service(self):
        name = self.strategy_var.get()
        if not name:
            messagebox.showwarning("Warning", "Select a strategy first")
            return
        if not is_admin():
            messagebox.showerror("Error", "Run as Administrator to install service")
            return
        if not messagebox.askyesno("Confirm", f"Install service with strategy '{name}'?"):
            return

        self._log(f"Installing service: {name}")

        bat_path = os.path.join(ZAPRET_DIR, f"{name}.bat")
        try:
            with open(bat_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            self._log(f"Error reading {name}.bat: {e}")
            return

        # Join continuation lines (^ at end)
        joined = ""
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.endswith("^"):
                joined += stripped[:-1].strip() + " "
            else:
                joined += stripped + " "

        # Find winws.exe and extract args
        lower = joined.lower()
        idx = lower.find("winws.exe")
        if idx == -1:
            self._log("Could not find winws.exe in bat file")
            return

        args = joined[idx + len("winws.exe"):].strip()

        # Replace batch variables
        bin_sl = BIN_DIR.replace("\\", "/")
        lists_sl = LISTS_DIR.replace("\\", "/")
        args = args.replace("%BIN%", bin_sl + "/")
        args = args.replace("%LISTS%", lists_sl + "/")
        args = args.replace("%%GameFilterTCP%%", "")
        args = args.replace("%%GameFilterUDP%%", "")
        args = args.replace("%GameFilterTCP%", "")
        args = args.replace("%GameFilterUDP%", "")
        args = " ".join(args.split())

        winws = os.path.join(BIN_DIR, "winws.exe")
        bin_path = f'{winws} {args}'

        self._log(f"binPath length: {len(bin_path)}")

        # Enable TCP timestamps
        run_cmd("netsh interface tcp set global timestamps=enabled")

        # Stop old service
        run_cmd("net stop zapret", timeout=10)
        run_cmd("sc delete zapret", timeout=10)

        # Stop old service
        run_cmd("net stop zapret", timeout=10)
        run_cmd("sc delete zapret", timeout=10)

        # Create service - use subprocess list to avoid all shell escaping
        winws = os.path.join(BIN_DIR, "winws.exe")
        sc_args = ["sc", "create", "zapret",
                   "binPath=", f'"{winws}" {args}',
                   "DisplayName=", "zapret",
                   "start=", "auto"]

        self._log(f"Running sc create (list)...")
        try:
            r = subprocess.run(sc_args, capture_output=True, timeout=15)
            out = r.stdout.decode("utf-8", errors="replace")
            err = r.stderr.decode("utf-8", errors="replace")
            result = out + err
        except Exception as e:
            result = str(e)
        self._log(f"sc create: {result.strip()[:300]}")

        # Description
        subprocess.run(["sc", "description", "zapret", "Zapret DPI bypass software"],
                       capture_output=True, timeout=10)

        # Start
        r = subprocess.run(["sc", "start", "zapret"], capture_output=True, timeout=15)
        result2 = r.stdout.decode("utf-8", errors="replace") + r.stderr.decode("utf-8", errors="replace")
        self._log(f"sc start: {result2.strip()[:200]}")

        run_cmd(f'reg add "HKLM\\System\\CurrentControlSet\\Services\\zapret" /v zapret-discord-youtube /t REG_SZ /d "{name}" /f')

        self.service_log.insert(tk.END, f"--- Install {name} ---\nsc create: {result.strip()[:300]}\nsc start: {result2.strip()[:200]}\n")
        self.service_log.see(tk.END)
        self.root.after(2000, self._refresh_status)

    def _remove_services(self):
        if not is_admin():
            messagebox.showerror("Error", "Run as Administrator to remove services")
            return
        if not messagebox.askyesno("Confirm", "Remove zapret service and WinDivert?"):
            return

        self._log("Removing service...")
        lines = []

        for cmd in ["net stop zapret", "sc delete zapret", "taskkill /IM winws.exe /F",
                     "net stop WinDivert", "sc delete WinDivert",
                     "net stop WinDivert14", "sc delete WinDivert14"]:
            out = run_cmd(cmd, timeout=15).strip()
            lines.append(f"{cmd}: {out}" if out else f"{cmd}: OK")

        self.service_log.insert(tk.END, "\n".join(lines) + "\n")
        self.service_log.see(tk.END)
        self._log("Service removed")
        self.active_strategy = None
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.root.after(1000, self._refresh_status)

    def _check_service_status(self):
        svc = get_service_status()
        winws_running = is_winws_running()
        msg = f"Service: {svc}\nwinws.exe: {'running' if winws_running else 'stopped'}"
        self.service_log.insert(tk.END, msg + "\n")
        self.service_log.see(tk.END)
        self._refresh_status()

    def _check_updates(self):
        self._log("Checking for updates...")
        result = run_cmd(f'"{SERVICE_BAT}" update', timeout=30)
        self.service_log.insert(tk.END, result + "\n")
        self.service_log.see(tk.END)

    def _update_ipset(self):
        self._log("Updating IPSet list...")
        result = run_cmd(f'"{SERVICE_BAT}" ipset', timeout=30)
        self.service_log.insert(tk.END, result + "\n")
        self.service_log.see(tk.END)

    def _update_hosts(self):
        self._log("Updating hosts file...")
        result = run_cmd(f'"{SERVICE_BAT}" hosts', timeout=30)
        self.service_log.insert(tk.END, result + "\n")
        self.service_log.see(tk.END)


if __name__ == "__main__":
    import tkinter.simpledialog
    root = tk.Tk()
    app = ZapretGUI(root)
    root.mainloop()
