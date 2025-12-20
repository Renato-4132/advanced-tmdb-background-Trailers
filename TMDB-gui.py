#!/usr/bin/env python3
import sys
import tkinter as tk
from tkinter import ttk, filedialog
import os, subprocess, re, threading, json, signal

try:
    from PIL import Image, ImageTk
except ImportError:
    ImageTk = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
PREFS_FILE = os.path.join(BASE_DIR, 'tmdb_gui_prefs.json')
CORE_SCRIPT = os.path.join(BASE_DIR, "TMDB.py")

COUNTRY_MAP = {
    "Afghanistan": "af", "Albania": "al", "Algeria": "dz", "Andorra": "ad",
    "Angola": "ao", "Antarctica": "aq", "Antigua and Barbuda": "ag", "Saudi Arabia": "sa",
    "Argentina": "ar", "Australia": "au", "Austria": "at", "Bahamas": "bs",
    "Belgium": "be", "Brazil": "br", "Canada": "ca", "Chile": "cl", "China": "cn",
    "Vatican City": "va", "Colombia": "co", "South Korea": "kr", "Croatia": "hr",
    "Cuba": "cu", "Denmark": "dk", "Egypt": "eg", "United Arab Emirates": "ae",
    "Finland": "fi", "France": "fr", "Germany": "de", "Greece": "gr",
    "India": "in", "Ireland": "ie", "Iceland": "is", "Italy": "it",
    "Mexico": "mx", "Norway": "no", "Netherlands": "nl", "Poland": "pl",
    "Portugal": "pt", "United Kingdom": "gb", "Czech Republic": "cz", "Romania": "ro",
    "Russia": "ru", "Spain": "es", "United States": "us", "Sweden": "se",
    "Switzerland": "ch", "Taiwan": "tw", "Turkey": "tr", "Ukraine": "ukr", "Uruguay": "uy"
}

class TMDBCliGui:
    def __init__(self, root):
        self.root = root
        self.root.title("TMDB FRONTEND")
        self.bg, self.fg, self.acc = "#121212", "#FFFFFF", "#2196F3"
        w, h = 700, 700
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        root.configure(bg=self.bg)
        self.process = None
        icon_path = os.path.join(BASE_DIR, "images", "tmdblogo.0.png")
        if ImageTk and os.path.exists(icon_path):
            try:
                self.win_icon = ImageTk.PhotoImage(Image.open(icon_path))
                self.root.iconphoto(True, self.win_icon)
            except: pass
        self.s = ttk.Style()
        self.s.theme_use('default')
        self.s.configure(".", font=("Arial", 8), background=self.bg, foreground="#888888")
        self.s.configure("TFrame", background=self.bg)
        self.s.configure("TLabel", background=self.bg, foreground="#888888")
        self.s.configure("Title.TLabel", foreground=self.acc, font=("Arial", 14, "bold"))
        self.s.configure("TEntry", 
           fieldbackground="#1e1e1e", 
           foreground="white", 
           insertcolor="white",
           borderwidth=0)
        self.s.map("TEntry", 
           foreground=[('disabled', '#888888'), ('active', 'white')],
           fieldbackground=[('readonly', '#1e1e1e')])
        self.s.configure("TCombobox", 
                         fieldbackground="#1e1e1e", 
                         foreground="white", 
                         insertcolor="white",
                         arrowcolor=self.acc,
                         borderwidth=0)
        self.s.map("TCombobox", 
                   fieldbackground=[('readonly', '#1e1e1e')], 
                   foreground=[('readonly', 'white')])
        self.s.configure("TCheckbutton", background=self.bg, foreground=self.acc)
        self.s.map("TCheckbutton", background=[('active', self.bg)])
        self.s.configure("Run.TButton", background="#4CAF50", foreground="white", font=("Arial", 8, "bold"))
        self.s.configure("Stop.TButton", background="#F44336", foreground="white", font=("Arial", 8, "bold"))
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        self.setup_ui(); self.load_prefs()
    def browse_path(self, e_w):
        p = filedialog.askdirectory()
        if p: e_w.delete(0, tk.END); e_w.insert(0, p + "/")
    def setup_ui(self):
        m = ttk.Frame(self.root, padding="10")
        m.grid(row=0, column=0, sticky="nsew")
        m.columnconfigure(0, weight=1); m.rowconfigure(5, weight=1)
        hf = ttk.Frame(m)
        hf.grid(row=0, column=0, pady=(0, 10), sticky="w")
        icon_path = os.path.join(BASE_DIR, "images", "tmdblogo.0.png")
        if ImageTk and os.path.exists(icon_path):
            img_p = Image.open(icon_path).convert("RGBA")
            img_p.thumbnail((24, 24))
            self.logo_img = ImageTk.PhotoImage(img_p)
            tk.Label(hf, image=self.logo_img, bg=self.bg).pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(hf, text="TMDB ENGINE FRONTEND PRO", style="Title.TLabel").pack(side=tk.LEFT)
        gf = ttk.Frame(m)
        gf.grid(row=1, column=0, sticky="ew")
        gf.columnconfigure(1, weight=1)
        def add_r(lbl, idx, var_name, browse=False):
            ttk.Label(gf, text=lbl).grid(row=idx, column=0, sticky="w", pady=2)
            e = ttk.Entry(gf)
            e.grid(row=idx, column=1, sticky="ew", padx=(10, 0), pady=2)
            if browse: ttk.Button(gf, text="...", width=3, command=lambda: self.browse_path(e)).grid(row=idx, column=2, padx=5)
            setattr(self, var_name, e); return e
        self.url_e = add_r("API URL:", 0, "url_e")
        self.auth_e = add_r("AUTH TOKEN:", 1, "auth_e")
        self.m_id_e = add_r("MOVIE ID:", 2, "m_id_e")
        self.tv_id_e = add_r("TV ID:", 3, "tv_id_e")
        self.limit_e = add_r("TREND LIMIT:", 4, "limit_e")
        ttk.Label(gf, text="COUNTRY:").grid(row=5, column=0, sticky="w", pady=2)
        self.count_c = ttk.Combobox(gf, values=list(COUNTRY_MAP.keys()), state="readonly")
        self.count_c.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=2)
        self.path_e = add_r("SAVE PATH:", 6, "path_e", True)
        self.dura_e = add_r("GIF DURA (ms):", 7, "dura_e")
        self.prog_e = add_r("TRAILER PROG:", 8, "prog_e")
        self.t_path_e = add_r("TRAILER PATH:", 9, "t_path_e", True)
        self.browser_e = add_r("BROWSER:", 10, "browser_e")
        of = ttk.Frame(m)
        of.grid(row=2, column=0, sticky="ew", pady=5)
        self.gif_v, self.dl_v, self.mr_v = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
        ttk.Checkbutton(of, text="Generate GIF", variable=self.gif_v).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(of, text="Download Trailers", variable=self.dl_v).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(of, text="Merge Trailers", variable=self.mr_v).pack(side=tk.LEFT, padx=5)
        self.out = tk.Text(m, bg="black", fg="white", font=("Arial", 8), relief="flat")
        self.out.grid(row=5, column=0, sticky="nsew", pady=5)
        bf = ttk.Frame(m)
        bf.grid(row=6, column=0, sticky="ew")
        self.run_btn = ttk.Button(bf, text="▶ RUN", style="Run.TButton", command=self.run)
        self.run_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=2)
        self.stop_btn = ttk.Button(bf, text="■ STOP", style="Stop.TButton", command=self.stop, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=2)
        ttk.Button(bf, text="SAVE", command=self.save).pack(side=tk.RIGHT, padx=2)
    def save(self):
        d = {"url": self.url_e.get(), "auth": self.auth_e.get(), "m_id": self.m_id_e.get(), "tv_id": self.tv_id_e.get(), "path": self.path_e.get(), "count": self.count_c.get(), "dura": self.dura_e.get(), "prog": self.prog_e.get(), "t_path": self.t_path_e.get(), "browser": self.browser_e.get(), "gif": self.gif_v.get(), "dl": self.dl_v.get(), "mr": self.mr_v.get(), "limit": self.limit_e.get()}
        with open(PREFS_FILE, "w") as f: json.dump(d, f, indent=4)
    def load_prefs(self):
        import platform
        py_cmd = sys.executable if platform.system() == "Windows" else "python3"
        defaults = {
            "url": "https://api.themoviedb.org/3",
            "auth": "",
            "m_id": "",
            "tv_id": "",
            "path": "tmdb_backgrounds/",
            "count": "Italy",
            "dura": "5000",
            "limit": "10",
            "prog": f"{py_cmd} -m yt_dlp",
            "t_path": "tmdb_trailers/",
            "browser": "firefox",
            "gif": False,
            "dl": False,
            "mr": False
        }
        data = defaults
        if os.path.exists(PREFS_FILE):
            try:
                with open(PREFS_FILE, "r") as f:
                    loaded_data = json.load(f)
                    data.update(loaded_data)
            except:
                pass
        self.url_e.insert(0, data.get("url", ""))
        self.auth_e.insert(0, data.get("auth", ""))
        self.m_id_e.insert(0, data.get("m_id", ""))
        self.tv_id_e.insert(0, data.get("tv_id", ""))
        self.path_e.insert(0, data.get("path", ""))
        self.count_c.set(data.get("count", "Italy"))
        self.dura_e.insert(0, data.get("dura", ""))
        self.limit_e.insert(0, data.get("limit", ""))
        self.prog_e.insert(0, data.get("prog", ""))
        self.t_path_e.insert(0, data.get("t_path", ""))
        self.browser_e.insert(0, data.get("browser", ""))
        self.gif_v.set(data.get("gif", False))
        self.dl_v.set(data.get("dl", False))
        self.mr_v.set(data.get("mr", False))
    def run(self):
        self.save(); self.out.delete('1.0', tk.END)
        self.run_btn.config(state="disabled"); self.stop_btn.config(state="normal")
        l_code = COUNTRY_MAP.get(self.count_c.get(), "us")
        import sys
        cmd = [sys.executable, "-u", CORE_SCRIPT, "--language", l_code]
        if self.limit_e.get(): cmd += ["--limit", self.limit_e.get()]
        if self.m_id_e.get().strip(): cmd += ["--movie-id", self.m_id_e.get().strip()]
        if self.tv_id_e.get().strip(): cmd += ["--tv-id", self.tv_id_e.get().strip()]
        if self.gif_v.get(): cmd += ["--gif-generate"]
        if self.dl_v.get(): cmd += ["--download-trailer"]
        if self.mr_v.get(): cmd += ["--merge-trailers"]
        threading.Thread(target=self.work, args=(cmd,), daemon=True).start()
    def stop(self):
        if self.process:
            import platform
            try:
                self.out.insert(tk.END, "\n[!] STOPPING PROCESS... PLEASE WAIT.\n")
                self.out.see(tk.END)
                if platform.system() == "Windows":
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.out.insert(tk.END, "[V] PROCESS TERMINATED.\n")
                self.out.see(tk.END)
            except Exception as e:
                self.out.insert(tk.END, f"\n[X] Error during stop: {e}\n")
            self.process = None
    def work(self, cmd):
        import platform
        try:
            cf = 0
            if platform.system() == "Windows":
                cf = 0x08000000 
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                start_new_session=True, 
                creationflags=cf
            )
            if self.process and self.process.stdout:
                for line in self.process.stdout:
                    c = re.sub(r'\x1b\[[0-9;]*m', '', line)
                    self.root.after(0, lambda l=c: (self.out.insert(tk.END, l), self.out.see(tk.END)))
                if self.process:
                    self.process.wait()
        except Exception as e:
            pass
        finally: 
            self.root.after(0, self.finish)
    def finish(self):
        self.run_btn.config(state="normal"); self.stop_btn.config(state="disabled"); self.process = None
if __name__ == "__main__":
    r = tk.Tk(); app = TMDBCliGui(r); r.mainloop()
