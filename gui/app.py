import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import os
import glob
import threading
import time
import hashlib

ZAPRET_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(ZAPRET_DIR, "bin")
LISTS_DIR = os.path.join(ZAPRET_DIR, "lists")
SERVICE_BAT = os.path.join(ZAPRET_DIR, "service.bat")


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=ZAPRET_DIR
        )
        return r.stdout + r.stderr
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
    backup = os.path.join(LISTS_DIR, "ipset-all.txt.backup")
    if not os.path.exists(ipset):
        return "none"
    size = os.path.getsize(ipset)
    if size < 100:
        with open(ipset, "r") as f:
            content = f.read().strip()
        if "203.0.113.113" in content:
            return "none"
        if content == "":
            return "any"
    return "loaded"


class ZapretGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zapret GUI Manager")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self.process = None
        self.strategies = get_strategies()
        self.strategy_names = [s[0] for s in self.strategies]

        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Green.TLabel", foreground="green", font=("Segoe UI", 10, "bold"))
        style.configure("Red.TLabel", foreground="red", font=("Segoe UI", 10, "bold"))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_main = ttk.Frame(notebook)
        tab_lists = ttk.Frame(notebook)
        tab_service = ttk.Frame(notebook)
        tab_log = ttk.Frame(notebook)

        notebook.add(tab_main, text="  Main  ")
        notebook.add(tab_lists, text="  Lists  ")
        notebook.add(tab_service, text="  Service  ")
        notebook.add(tab_log, text="  Log  ")

        self._build_main_tab(tab_main)
        self._build_lists_tab(tab_lists)
        self._build_service_tab(tab_service)
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

        row2 = ttk.Frame(status_frame)
        row2.pack(fill=tk.X)
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
        self.btn_refresh = ttk.Button(row8, text="Refresh Status", command=self._refresh_status, width=18)
        self.btn_refresh.pack(side=tk.LEFT)
        self.btn_diag = ttk.Button(row8, text="Run Diagnostics", command=self._run_diagnostics, width=18)
        self.btn_diag.pack(side=tk.LEFT, padx=(10, 0))

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
        domain_files = [
            "list-general.txt",
            "list-general-user.txt",
            "list-exclude.txt",
            "list-google.txt",
        ]
        for f in domain_files:
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
        btn = ttk.Button(parent, text="Clear Log", command=lambda: self.log_text.delete("1.0", tk.END))
        btn.pack(pady=(0, 10))

    def _log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)

    def _refresh_status(self):
        svc = get_service_status()
        gf = get_game_filter_status()
        ipset = get_ipset_status()
        winws_running = "winws.exe" in run_cmd("tasklist /FI \"IMAGENAME eq winws.exe\"", timeout=5)

        self.lbl_service.config(text=svc.upper(), style="Green.TLabel" if svc == "running" else "Red.TLabel")
        self.lbl_game.config(text=gf)
        self.lbl_ipset.config(text=ipset)
        self.lbl_winws.config(text="RUNNING" if winws_running else "STOPPED", style="Green.TLabel" if winws_running else "Red.TLabel")

        self.game_filter_var.set(gf)
        self.ipset_var.set(ipset)
        self._log(f"Status refreshed: service={svc}, winws={'running' if winws_running else 'stopped'}, game={gf}, ipset={ipset}")

    def _start_strategy(self):
        name = self.strategy_var.get()
        if not name:
            messagebox.showwarning("Warning", "Select a strategy first")
            return
        strategy_path = os.path.join(ZAPRET_DIR, f"{name}.bat")
        if not os.path.exists(strategy_path):
            messagebox.showerror("Error", f"File not found: {strategy_path}")
            return

        self._stop_strategy()
        self._log(f"Starting strategy: {name}")
        self.process = subprocess.Popen(
            f'cmd /c "{strategy_path}"', shell=True, cwd=ZAPRET_DIR, creationflags=subprocess.CREATE_NO_WINDOW
        )
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self._log(f"Strategy {name} started (PID: {self.process.pid})")
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
        self._log(f"Game Filter set to: {val}")

    def _set_ipset_filter(self):
        val = self.ipset_var.get()
        ipset = os.path.join(LISTS_DIR, "ipset-all.txt")
        backup = os.path.join(LISTS_DIR, "ipset-all.txt.backup")

        if val == "none":
            if os.path.exists(ipset) and os.path.exists(backup):
                if os.path.getsize(ipset) > 100:
                    os.replace(ipset, backup)
            with open(ipset, "w") as f:
                f.write("203.0.113.113/32\n")
        elif val == "any":
            if os.path.exists(ipset):
                size = os.path.getsize(ipset)
                if size > 100 and "203.0.113.113" not in open(ipset).read():
                    os.replace(ipset, backup)
            with open(ipset, "w") as f:
                f.write("")
        elif val == "loaded":
            if os.path.exists(backup) and os.path.getsize(backup) > 100:
                os.replace(backup, ipset)
        self._log(f"IPSet Filter set to: {val}")

    def _run_diagnostics(self):
        self._log("Running diagnostics...")
        result = run_cmd(f'"{SERVICE_BAT}" diagnostics', timeout=60)
        self._log(result[:2000] if result else "No output")

    def _on_domain_select(self, event):
        selection = self.domain_listbox.curselection()
        if not selection:
            return
        filename = self.domain_listbox.get(selection[0])
        filepath = os.path.join(LISTS_DIR, filename)
        self._current_domain_file = filepath
        self.domain_text.delete("1.0", tk.END)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
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
        domain = tk.simpledialog.askstring("Add Domain", "Enter domain:")
        if domain:
            self.domain_text.insert(tk.END, domain.strip() + "\n")
            self._save_domain_list()

    def _remove_domain(self):
        if not self._current_domain_file:
            return
        sel = self.domain_text.tag_ranges(tk.SEL)
        if sel:
            self.domain_text.delete(sel[0], sel[1])

    def _install_service(self):
        self._log("Installing service...")
        result = run_cmd(f'echo 1 | "{SERVICE_BAT}" install', timeout=30)
        self.service_log.insert(tk.END, result + "\n")
        self.service_log.see(tk.END)
        self._log("Service installation initiated")
        self._refresh_status()

    def _remove_services(self):
        if messagebox.askyesno("Confirm", "Remove zapret service?"):
            self._log("Removing service...")
            result = run_cmd(f'echo 1 | "{SERVICE_BAT}" remove', timeout=30)
            self.service_log.insert(tk.END, result + "\n")
            self.service_log.see(tk.END)
            self._refresh_status()

    def _check_service_status(self):
        self._log("Checking service status...")
        svc = get_service_status()
        winws_running = "winws.exe" in run_cmd("tasklist /FI \"IMAGENAME eq winws.exe\"", timeout=5)
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
