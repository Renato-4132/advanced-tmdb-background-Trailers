#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk, GLib, Gio
import os
import subprocess
import re
import threading
import json
import webbrowser

SCRIPTS = {
    "TMDB-cli.py": os.path.abspath('./TMDB-cli.py'),
    "TMDB.py": os.path.abspath('./TMDB.py')
}
LOGO_PATH = os.path.abspath('./images/tmdblogo.1.png')
COUNTRY_CODES_PDF = os.path.abspath('./app/Country Codes ISO-3166.pdf')

DEFAULT_PREFS_FOLDER = os.path.abspath('./app/')
DEFAULT_PREFS_FILE = os.path.join(DEFAULT_PREFS_FOLDER, 'tmdb_gui_prefs.json')
COOKIES_VALUE = "--cookies-from-browser"

def ensure_prefs_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1b\[([0-9;]*[mK])')
    return ansi_escape.sub('', text)

def strip_date_time_lines(text):
    plain = strip_ansi_codes(text)
    if re.search(r'(date:|time:|hour:)', plain, re.IGNORECASE):
        return ''
    return text

class TMDBCliGui:
    def __init__(self):
        self.prefs_folder = DEFAULT_PREFS_FOLDER
        self.prefs_file = DEFAULT_PREFS_FILE

        ensure_prefs_folder(self.prefs_folder)

        self.window = gtk.Window(title="TMDB Background & Trailer GUI")
        self.window.set_border_width(12)
        self.window.set_default_size(700, 320)  # reduced height
        self.window.set_resizable(True)
        self.window.connect("destroy", gtk.main_quit)

        grid = gtk.Grid(row_spacing=8, column_spacing=8)
        self.window.add(grid)

        if os.path.exists(LOGO_PATH):
            logo_img = gtk.Image.new_from_file(LOGO_PATH)
            grid.attach(logo_img, 0, 0, 1, 1)
            base_row = 1
        else:
            base_row = 0

        self.movie_id_entry = gtk.Entry()
        grid.attach(gtk.Label(label="Movie ID:"), 0, base_row, 1, 1)
        grid.attach(self.movie_id_entry, 1, base_row, 2, 1)

        self.tv_id_entry = gtk.Entry()
        grid.attach(gtk.Label(label="TV Show ID:"), 0, base_row+1, 1, 1)
        grid.attach(self.tv_id_entry, 1, base_row+1, 2, 1)

        self.language_entry = gtk.Entry()
        self.language_entry.set_text("it")
        language_label = gtk.Label(label="Language:")

        help_button = gtk.Button(label="Help")
        help_button.set_tooltip_text("Open Country Codes ISO-3166.pdf")
        help_button.connect("clicked", self.on_help_clicked)

        grid.attach(language_label, 0, base_row+2, 1, 1)
        grid.attach(self.language_entry, 1, base_row+2, 1, 1)
        grid.attach(help_button, 2, base_row+2, 1, 1)

        self.save_path_entry = gtk.Entry()
        self.save_path_entry.set_text("tmdb_backgrounds/")
        grid.attach(gtk.Label(label="Save Path:"), 0, base_row+3, 1, 1)
        grid.attach(self.save_path_entry, 1, base_row+3, 1, 1)
        self.save_path_delete_btn = gtk.Button(label="Delete")
        self.save_path_delete_btn.set_tooltip_text("Delete the folder set as Save Path")
        self.save_path_delete_btn.connect("clicked", self.on_delete_save_path_clicked)
        grid.attach(self.save_path_delete_btn, 2, base_row+3, 1, 1)

        self.gif_generate_check = gtk.CheckButton(label="Generate GIF (adds -gif-gen option)")
        grid.attach(self.gif_generate_check, 0, base_row+4, 2, 1)

        self.dura_entry = gtk.Entry()
        self.dura_entry.set_text("5000")
        grid.attach(gtk.Label(label="GIF Timing (ms):"), 0, base_row+5, 1, 1)
        grid.attach(self.dura_entry, 1, base_row+5, 2, 1)

        self.dl_trailer_check = gtk.CheckButton(label="Download YouTube Trailer (adds -download-trailer option)")
        grid.attach(self.dl_trailer_check, 0, base_row+6, 2, 1)

        self.trailer_program_entry = gtk.Entry()
        self.trailer_program_entry.set_text("yt-dlp")
        grid.attach(gtk.Label(label="Trailer Program:"), 0, base_row+7, 1, 1)
        grid.attach(self.trailer_program_entry, 1, base_row+7, 2, 1)

        self.trailer_save_path_entry = gtk.Entry()
        self.trailer_save_path_entry.set_text("tmdb_trailers/")
        grid.attach(gtk.Label(label="Trailer Save Path:"), 0, base_row+8, 1, 1)
        grid.attach(self.trailer_save_path_entry, 1, base_row+8, 1, 1)
        self.trailer_save_path_delete_btn = gtk.Button(label="Delete")
        self.trailer_save_path_delete_btn.set_tooltip_text("Delete the folder set as Trailer Save Path")
        self.trailer_save_path_delete_btn.connect("clicked", self.on_delete_trailer_save_path_clicked)
        grid.attach(self.trailer_save_path_delete_btn, 2, base_row+8, 1, 1)

        self.youtube_cookies_entry = gtk.Entry()
        self.youtube_cookies_entry.set_text(COOKIES_VALUE)
        self.youtube_cookies_entry.set_editable(False)
        grid.attach(gtk.Label(label="YouTube Cookies:"), 0, base_row+9, 1, 1)
        grid.attach(self.youtube_cookies_entry, 1, base_row+9, 2, 1)

        self.default_browser_entry = gtk.Entry()
        self.default_browser_entry.set_text("firefox")
        grid.attach(gtk.Label(label="Default Browser:"), 0, base_row+10, 1, 1)
        grid.attach(self.default_browser_entry, 1, base_row+10, 2, 1)

        self.merge_trailers_check = gtk.CheckButton(label="Merge all trailers into one movie.mp4 (adds -merge-trailers option)")
        grid.attach(self.merge_trailers_check, 0, base_row+11, 2, 1)

        grid.attach(gtk.Label(label="Script to Run:"), 0, base_row+12, 1, 1)
        self.script_combo = gtk.ComboBoxText()
        self.script_combo.append_text("TMDB-cli.py")
        self.script_combo.append_text("TMDB.py")
        self.script_combo.set_active(0)
        grid.attach(self.script_combo, 1, base_row+12, 2, 1)

        grid.attach(gtk.Label(label="Preferences Save Path:"), 0, base_row+13, 1, 1)
        self.prefs_path_entry = gtk.Entry()
        self.prefs_path_entry.set_text(self.prefs_folder)
        grid.attach(self.prefs_path_entry, 1, base_row+13, 2, 1)

        self.output_buffer = gtk.TextBuffer()
        self.output_view = gtk.TextView(buffer=self.output_buffer)
        self.output_view.set_editable(False)
        self.output_view.set_cursor_visible(False)
        self.output_view.set_wrap_mode(gtk.WrapMode.WORD_CHAR)

        # Persistent end mark
        self.output_end_mark = self.output_buffer.create_mark("output_end", self.output_buffer.get_end_iter(), True)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_min_content_height(120)  # reduced height for less tall window
        scrolled.set_min_content_width(650)
        scrolled.add(self.output_view)
        grid.attach(scrolled, 0, base_row+14, 3, 1)

        # --- Bottom buttons in an HBox to shrink ---
        button_box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=4)
        grid.attach(button_box, 0, base_row+15, 3, 1)

        self.run_btn = gtk.Button(label="Run Script")
        self.run_btn.set_size_request(1, 1)
        self.run_btn.connect("clicked", self.on_run_clicked)
        button_box.pack_start(self.run_btn, False, False, 0)

        self.stop_btn = gtk.Button(label="Stop")
        self.stop_btn.set_tooltip_text("Stop the running process")
        self.stop_btn.set_size_request(1, 1)
        self.stop_btn.connect("clicked", self.on_stop_clicked)
        button_box.pack_start(self.stop_btn, False, False, 0)

        self.save_prefs_btn = gtk.Button(label="Save Preferences")
        self.save_prefs_btn.set_tooltip_text("Save current arguments and mode to prefs file in chosen folder")
        self.save_prefs_btn.set_size_request(1, 1)
        self.save_prefs_btn.connect("clicked", self.on_save_prefs_clicked)
        button_box.pack_start(self.save_prefs_btn, False, False, 0)

        self.dark_mode = False
        self.toggle_dark_btn = gtk.Button(label="Toggle Dark/Clear Mode")
        self.toggle_dark_btn.set_tooltip_text("Toggle between dark and light (clear) mode")
        self.toggle_dark_btn.set_size_request(1, 1)
        self.toggle_dark_btn.connect("clicked", self.on_toggle_dark_mode)
        button_box.pack_start(self.toggle_dark_btn, False, False, 0)

        self.process = None
        self.process_lock = threading.Lock()

        self.load_prefs_from_file()
        self.window.show_all()

    def on_toggle_dark_mode(self, widget):
        self.dark_mode = not self.dark_mode
        settings = gtk.Settings.get_default()
        if self.dark_mode:
            settings.set_property("gtk-theme-name", "Adwaita-dark")
        else:
            settings.set_property("gtk-theme-name", "Adwaita")

    def on_help_clicked(self, widget):
        if os.path.exists(COUNTRY_CODES_PDF):
            subprocess.Popen(["xdg-open", COUNTRY_CODES_PDF])
        else:
            dialog = gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=gtk.MessageType.ERROR,
                buttons=gtk.ButtonsType.OK,
                text="Country Codes PDF not found!",
            )
            dialog.format_secondary_text(COUNTRY_CODES_PDF)
            dialog.run()
            dialog.destroy()

    def on_delete_save_path_clicked(self, widget):
        folder = self.save_path_entry.get_text().strip()
        if folder and os.path.isdir(folder):
            try:
                import shutil
                shutil.rmtree(folder)
                self.append_output(f"Deleted folder: {folder}\n")
            except Exception as e:
                self.append_output(f"Error deleting folder {folder}: {e}\n")
        else:
            self.append_output(f"No valid folder to delete: {folder}\n")

    def on_delete_trailer_save_path_clicked(self, widget):
        folder = self.trailer_save_path_entry.get_text().strip()
        if folder and os.path.isdir(folder):
            try:
                import shutil
                shutil.rmtree(folder)
                self.append_output(f"Deleted folder: {folder}\n")
            except Exception as e:
                self.append_output(f"Error deleting folder {folder}: {e}\n")
        else:
            self.append_output(f"No valid folder to delete: {folder}\n")

    def on_run_clicked(self, widget):
        movie_id = self.movie_id_entry.get_text().strip()
        tv_id = self.tv_id_entry.get_text().strip()
        if movie_id or tv_id:
            script_choice = "TMDB-cli.py"
            self.script_combo.set_active(0)
        else:
            script_choice = "TMDB.py"
            self.script_combo.set_active(1)
        script_path = SCRIPTS.get(script_choice, SCRIPTS["TMDB-cli.py"])
        cmd = ["python3", "-u", script_path]

        self.output_buffer.set_text("")
        self.output_end_mark = self.output_buffer.create_mark("output_end", self.output_buffer.get_end_iter(), True)

        language = self.language_entry.get_text().strip()
        save_path = self.save_path_entry.get_text().strip()
        gif_generate = self.gif_generate_check.get_active()
        dura = self.dura_entry.get_text().strip()
        dl_trailer = self.dl_trailer_check.get_active()
        trailer_program = self.trailer_program_entry.get_text().strip()
        trailer_save_path = self.trailer_save_path_entry.get_text().strip()
        default_browser = self.default_browser_entry.get_text().strip()
        merge_trailers = self.merge_trailers_check.get_active()

        if language:
            cmd += ["-language", language]
        if save_path:
            cmd += ["-save-path", save_path]
        if gif_generate:
            cmd += ["-gif-gen"]
        if dura:
            cmd += ["-dura", dura]
        if dl_trailer:
            cmd += ["-download-trailer"]
        if trailer_program:
            cmd += ["-trailer-program", trailer_program]
        if trailer_save_path:
            cmd += ["-trailer-save-path", trailer_save_path]
        if default_browser:
            cmd += ["-default-browser", default_browser]
        if merge_trailers:
            cmd += ["-merge-trailers"]
        if movie_id:
            cmd += ["-movie-id", movie_id]
        if tv_id:
            cmd += ["-tv-id", tv_id]

        self.append_output(f"Running: {' '.join(cmd)}\n")
        self.run_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)

        threading.Thread(target=self.run_process, args=(cmd,), daemon=True).start()

    def run_process(self, cmd):
        try:
            env = os.environ.copy()
            if 'TERM' not in env:
                env['TERM'] = 'xterm'
            with self.process_lock:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    env=env 
                )
                proc = self.process

            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                clean_line = strip_ansi_codes(line)
                filtered = strip_date_time_lines(clean_line)
                if filtered.strip():
                    GLib.idle_add(self.append_output, filtered)
            proc.wait()
            if proc.returncode == 0:
                GLib.idle_add(self.append_output, "Done!\n")
            else:
                GLib.idle_add(self.append_output, f"Exited with code {proc.returncode}\n")
        except Exception as e:
            GLib.idle_add(self.append_output, f"Error: {e}\n")
        finally:
            with self.process_lock:
                self.process = None
            GLib.idle_add(self.run_btn.set_sensitive, True)
            GLib.idle_add(self.stop_btn.set_sensitive, False)

    def on_stop_clicked(self, widget):
        with self.process_lock:
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.append_output("Stopped process (SIGTERM sent).\n")
                except Exception as e:
                    self.append_output(f"Error stopping process: {e}\n")
            else:
                self.append_output("No running process to stop.\n")

    def append_output(self, text):
        end_iter = self.output_buffer.get_end_iter()
        self.output_buffer.insert(end_iter, text)
        self.output_buffer.move_mark(self.output_end_mark, self.output_buffer.get_end_iter())
        self.output_view.scroll_to_mark(self.output_end_mark, 0.0, True, 0.0, 1.0)

    def on_save_prefs_clicked(self, widget):
        prefs_folder = self.prefs_path_entry.get_text().strip()
        if not prefs_folder:
            prefs_folder = DEFAULT_PREFS_FOLDER
        prefs_file = os.path.join(prefs_folder, 'tmdb_gui_prefs.json')
        ensure_prefs_folder(prefs_folder)
        prefs = {
            "dark_mode": self.dark_mode,
            "movie_id": self.movie_id_entry.get_text(),
            "tv_id": self.tv_id_entry.get_text(),
            "language": self.language_entry.get_text(),
            "save_path": self.save_path_entry.get_text(),
            "gif_generate": self.gif_generate_check.get_active(),
            "dura": self.dura_entry.get_text(),
            "dl_trailer": self.dl_trailer_check.get_active(),
            "trailer_program": self.trailer_program_entry.get_text(),
            "trailer_save_path": self.trailer_save_path_entry.get_text(),
            "default_browser": self.default_browser_entry.get_text(),
            "merge_trailers": self.merge_trailers_check.get_active(),
            "script_index": self.script_combo.get_active(),
            "prefs_folder": prefs_folder
        }
        try:
            with open(prefs_file, "w") as f:
                json.dump(prefs, f, indent=2)
            self.append_output(f"Preferences saved to {prefs_file}\n")
        except Exception as e:
            self.append_output(f"Failed to save preferences: {e}\n")

    def load_prefs_from_file(self):
        prefs_folder = DEFAULT_PREFS_FOLDER
        prefs_file = os.path.join(prefs_folder, 'tmdb_gui_prefs.json')
        if not os.path.exists(prefs_file):
            return
        try:
            with open(prefs_file, "r") as f:
                prefs = json.load(f)
            self.prefs_path_entry.set_text(prefs.get("prefs_folder", prefs_folder))
            self.dark_mode = prefs.get("dark_mode", False)
            settings = gtk.Settings.get_default()
            if self.dark_mode:
                settings.set_property("gtk-theme-name", "Adwaita-dark")
            else:
                settings.set_property("gtk-theme-name", "Adwaita")
            self.movie_id_entry.set_text(prefs.get("movie_id", ""))
            self.tv_id_entry.set_text(prefs.get("tv_id", ""))
            self.language_entry.set_text(prefs.get("language", "it"))
            self.save_path_entry.set_text(prefs.get("save_path", "tmdb_backgrounds/"))
            self.gif_generate_check.set_active(prefs.get("gif_generate", False))
            self.dura_entry.set_text(prefs.get("dura", "5000"))
            self.dl_trailer_check.set_active(prefs.get("dl_trailer", False))
            self.trailer_program_entry.set_text(prefs.get("trailer_program", "yt-dlp"))
            self.trailer_save_path_entry.set_text(prefs.get("trailer_save_path", "tmdb_trailers/"))
            self.default_browser_entry.set_text(prefs.get("default_browser", "firefox"))
            self.merge_trailers_check.set_active(prefs.get("merge_trailers", False))
            script_index = prefs.get("script_index", 0)
            self.script_combo.set_active(script_index)
            self.append_output(f"Loaded preferences from {prefs_file}\n")
        except Exception as e:
            self.append_output(f"Failed to load preferences: {e}\n")

if __name__ == "__main__":
    TMDBCliGui()
    gtk.main()
