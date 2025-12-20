#!/usr/bin/env python3

import subprocess
import sys
import os
import shutil
import platform
import sys

WHITE_COLOR = "\033[97m"
RED_COLOR = "\033[91m"
YELLOW_COLOR = "\033[93m"
GREEN_COLOR = "\033[92m"
RESET = "\033[0m"

def initialize_environment():
    required_py = {
        "requests": "requests",
        "PIL": "Pillow",
        "imageio": "imageio",
        "numpy": "numpy",
        "yt_dlp": "yt-dlp"
    }
    missing_py = []
    for mod, pkg in required_py.items():
        try:
            if mod == "PIL":
                __import__("PIL.Image")
            else:
                __import__(mod)
        except ImportError:
            missing_py.append(pkg)
    if missing_py:
        print(f"{YELLOW_COLOR}[!] Missing Python dependencies: {', '.join(missing_py)}{RESET}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_py])
            print(f"{GREEN_COLOR}[V] Python libraries installed successfully.{RESET}")
        except Exception as e:
            print(f"{RED_COLOR}[X] Error during library installation: {e}{RESET}")
            sys.exit(1)
    if not shutil.which("ffmpeg"):
        print(f"{YELLOW_COLOR}[!] WARNING: FFmpeg not found.{RESET}")
        if platform.system() == "Windows":
            print(f"{WHITE_COLOR}--> Please download ffmpeg from gyan.dev and add it to PATH.{RESET}")
        else:
            print(f"{WHITE_COLOR}--> Install it with: sudo apt install ffmpeg{RESET}")
initialize_environment()

import requests
from PIL import Image, ImageDraw, ImageFont
import imageio
import numpy as np
import json
import argparse
import textwrap
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREFS_FILE = os.path.join(BASE_DIR, 'tmdb_gui_prefs.json')
LIMIT = 10
py_cmd = sys.executable if platform.system() == "Windows" else "python3"

def check_fonts():
    font_dir = os.path.join(BASE_DIR, "fonts")
    font_path = os.path.join(font_dir, "Roboto-Light.ttf")
    if not os.path.exists(font_path):
        print(f"{YELLOW_COLOR}[!] Font not found. Creating directory and downloading...{RESET}")
        os.makedirs(font_dir, exist_ok=True)
        font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            import requests
            response = requests.get(font_url, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(response.content)
                print(f"{GREEN_COLOR}[V] Font downloaded successfully: {font_path}{RESET}")
            else:
                print(f"{RED_COLOR}[X] Failed to download font. Status code: {response.status_code}{RESET}")
                print(f"{YELLOW_COLOR}[!] Manually place 'Roboto-Light.ttf' inside {font_dir}{RESET}")
        except Exception as e:
            print(f"{RED_COLOR}[X] Error downloading font: {e}{RESET}")

def load_prefs():
    defaults = {
        "api_url": "https://api.themoviedb.org/3/",
        "api_auth": "",
        "language": "en-US",
        "save_path": "tmdb_backgrounds/",
        "duration": 5000,
        "trailer_program": "yt-dlp",
        "trailer_save_path": "tmdb_trailers/",
        "browser": "firefox",
        "limit": 10
    }
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r") as f:
                data = json.load(f)
                if "url" in data: defaults["api_url"] = data["url"]
                if "auth" in data: defaults["api_auth"] = data["auth"]
                if "path" in data: defaults["save_path"] = data["path"]
                if "dura" in data: defaults["duration"] = int(data["dura"])
                if "prog" in data: defaults["trailer_program"] = data["prog"]
                if "t_path" in data: defaults["trailer_save_path"] = data["t_path"]
                if "browser" in data: defaults["browser"] = data["browser"]
                if "limit" in data: defaults["limit"] = int(data["limit"])
                return defaults
        except: pass
    return defaults

prefs = load_prefs()
parser = argparse.ArgumentParser(description="TMDB Engine Core")
parser.add_argument('--api-url', default=prefs.get("api_url", ""))
parser.add_argument('--api-auth', default=prefs.get("api_auth", ""))
parser.add_argument('--language', default=prefs.get("language", "it-IT"))
parser.add_argument('--save-path', default=prefs.get("save_path", "tmdb_backgrounds/"))
parser.add_argument('--movie-id', type=str, default="")
parser.add_argument('--tv-id', type=str, default="")
parser.add_argument('--gif-generate', '-gif-generate', action='store_true')
parser.add_argument('--dura', type=int, default=int(prefs.get("duration", 5000)))
parser.add_argument('--download-trailer', action='store_true')
parser.add_argument('--merge-trailers', action='store_true')
parser.add_argument('--trailer-save-path', default=prefs.get("trailer_save_path", "tmdb_trailers/"))
parser.add_argument('--trailer-program', default=prefs.get("prog", f"{py_cmd} -m yt_dlp"))
parser.add_argument('--default-browser', default=prefs.get("browser", "firefox"))
parser.add_argument('--limit', type=int, default=int(prefs.get("limit", 10)))
args = parser.parse_args()
do_merge = args.merge_trailers or getattr(args, 'merge_trailers', False)
do_gif = args.gif_generate
do_merge = args.merge_trailers or getattr(args, 'merge_trailers', False)
do_gif = args.gif_generate
auth = args.api_auth if "Bearer" in args.api_auth else f"Bearer {args.api_auth}"
HEADERS = {"accept": "application/json", "Authorization": auth}
def clean_filename(t):
    text_with_underscores = t.replace(" ", "_")
    return "".join(c for c in text_with_underscores if c.isalnum() or c == "_")

def get_data(endpoint):
    url = f"{args.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        r = requests.get(url, headers=HEADERS, params={"language": args.language}, timeout=10)
        T_PATH = args.trailer_save_path
        return r.json() if r.status_code == 200 else {}
    except: return {}
def get_logo(mtype, mid):
    lang_short = args.language.split('-')[0]
    endpoint = f"{mtype}/{mid}/images?include_image_language={lang_short},en,null"
    data = get_data(endpoint)
    logos = data.get("logos", [])
    if not logos:
        return None
    for l in logos:
        if l.get("iso_639_1") == lang_short and l.get("file_path", "").endswith(".png"):
            return l["file_path"]
    for l in logos:
        if l.get("file_path", "").endswith(".png"):
            return l["file_path"]
    return None
def process_item(item, mtype):
    font_path = os.path.join(BASE_DIR, "fonts", "Roboto-Light.ttf")
    if not os.path.exists(font_path):
        check_fonts()
    if not item or "id" not in item: return
    is_movie = (mtype == "movie")
    title = item.get('title') if is_movie else item.get('name')
    if any(ord(c) > 255 for c in title):
        print(f"{YELLOW_COLOR}[!] Unsupported characters in title ({title}), fetching US version...{RESET}")
        fb_url = f"{args.api_url.rstrip('/')}/{mtype}/{item['id']}"
        fb_res = requests.get(fb_url, headers=HEADERS, params={"language": "en-US"}, timeout=10)
        if fb_res.status_code == 200:
            data_us = fb_res.json()
            title = data_us.get('title') if is_movie else data_us.get('name')
            print(f"{GREEN_COLOR}[V] New title: {title}{RESET}")
    if not title: return
    print(f"{GREEN_COLOR}Processing: {WHITE_COLOR}{title}{RESET}")
    
    path = item.get('backdrop_path')
    if path:
        try:
            img_resp = requests.get(f"https://image.tmdb.org/t/p/original{path}")
            main_img = Image.open(BytesIO(img_resp.content)).convert("RGBA")
            h_target = 1500
            w_target = int(main_img.width * (h_target / main_img.height))
            main_img = main_img.resize((w_target, h_target))
            img_dir = os.path.join(BASE_DIR, "images")
            font_path = os.path.join(BASE_DIR, "fonts", "Roboto-Light.ttf")
            bckg = Image.open(os.path.join(img_dir, "bckg.png")).convert("RGBA")
            overlay = Image.open(os.path.join(img_dir, "overlay.png")).convert("RGBA")
            tmdblogo = Image.open(os.path.join(img_dir, "tmdblogo.png")).convert("RGBA")
            bckg.paste(main_img, (1175, 0), main_img)
            bckg.paste(overlay, (1175, 0), overlay)
            bckg.paste(tmdblogo, (680, 1115), tmdblogo)
            draw = ImageDraw.Draw(bckg)
            f_title = ImageFont.truetype(font_path, 180)
            f_desc = ImageFont.truetype(font_path, 50)
            rating = f"TMDB: {round(item.get('vote_average', 0), 1)}"
            year = (item.get('release_date') if is_movie else item.get('first_air_date')) or "N/A"
            info_line = f"{year[:4]}  •  {rating}"
            draw.text((210, 650), info_line, font=f_desc, fill=(180, 180, 180))
            ov = item.get('overview', '')
            if not ov or len(ov.strip()) < 10:
                edit_link = f"https://www.themoviedb.org/{mtype}/{item['id']}/edit?language={args.language}"
                print(f"{YELLOW_COLOR}[!] Plot missing. Edit it here: --> {edit_link}{RESET}")
                print(f"{YELLOW_COLOR}[!] Plot missing/short in '{args.language}', fetching 'en-US' fallback...{RESET}")
                try:
                    fb_url = f"{args.api_url.rstrip('/')}/{mtype}/{item['id']}"
                    fb_res = requests.get(fb_url, headers=HEADERS, params={"language": "en-US"}, timeout=10)
                    if fb_res.status_code == 200:
                        ov = fb_res.json().get('overview', '')
                except Exception as e:
                    print(f"{RED_COLOR}Fallback error: {e}{RESET}")
            if not ov or len(ov.strip()) < 5:
                ov = "Description not available in the selected language or English."
            lines = textwrap.wrap(ov, width=65, max_lines=5, placeholder="...")
            wrapped = "\n".join(lines) if lines else ov
            draw.text((210, 730), wrapped, font=f_desc, fill="white")
            draw.text((210, 1100), "Now trending on", font=f_desc, fill="white")
            lp = get_logo(mtype, item['id'])
            if lp:
                l_img = Image.open(BytesIO(requests.get(f"https://image.tmdb.org/t/p/original{lp}").content)).convert("RGBA")
                l_img.thumbnail((1000, 450))
                bckg.paste(l_img, (210, 580 - l_img.height), l_img)
            else:
                draw.text((210, 400), title[:30].upper(), font=f_title, fill="white")
            os.makedirs(args.save_path, exist_ok=True)
            bckg.convert("RGB").save(os.path.join(args.save_path, f"{clean_filename(title)}.jpg"))
        except Exception as e:
            print(f"{RED_COLOR}Graphics Error: {e}{RESET}")
    if args.download_trailer:
        v_data = get_data(f"{mtype}/{item['id']}/videos")
        for v in v_data.get("results", []):
            if v.get("site") == "YouTube":
                t_url = f"https://www.youtube.com/watch?v={v['key']}"
                os.makedirs(args.trailer_save_path, exist_ok=True)
                out = os.path.join(args.trailer_save_path, f"{clean_filename(title)}.mp4")
                full_cmd = args.trailer_program.split() + [
                    "--cookies-from-browser", args.default_browser, 
                    t_url, 
                    "-o", out
                ]
                try:
                    subprocess.run(full_cmd, check=True)
                except Exception as e:
                    print(f"{RED_COLOR}Error download: {e}{RESET}")
                break
if args.movie_id:
    process_item(get_data(f"movie/{args.movie_id}"), "movie")
elif args.tv_id:
    process_item(get_data(f"tv/{args.tv_id}"), "tv")
else:
    print(f"{YELLOW_COLOR}Trending Mode (Limit: {args.limit})...{RESET}")
    trend = get_data("trending/movie/week").get("results", [])
    for m in trend[:args.limit]: process_item(m, "movie")
if args.gif_generate:
    print(f"\n{YELLOW_COLOR}Generating GIF...{RESET}")
    files = sorted([os.path.join(args.save_path, f) for f in os.listdir(args.save_path) if f.endswith(".jpg")])
    if files:
        images = []
        for f in files:
            img = Image.open(f).resize((1920, 1080))
            images.append(np.array(img.convert("RGB")))
        gif_out = os.path.join(args.save_path, "Movie_output.gif")
        frame_duration = int(args.dura) 
        imageio.mimsave(gif_out, images, duration=frame_duration, loop=0)
        print(f"{GREEN_COLOR}GIF Created: {gif_out} ({frame_duration}ms per frame){RESET}")
if args.merge_trailers:
    target_dir = args.trailer_save_path
    print(f"\n{YELLOW_COLOR}Starting trailer merge process in: {target_dir}{RESET}")
    if not os.path.exists(target_dir):
        print(f"{RED_COLOR}[X] Error: Trailer directory not found!{RESET}")
    else:
        video_files = sorted([f for f in os.listdir(target_dir) if f.endswith('.mp4') and f != "FINAL_TRAILER_COLLECTION.mp4"])
        if len(video_files) > 1:
            list_path = os.path.join(target_dir, "inputs.txt")
            with open(list_path, "w") as f:
                for video in video_files:
                    f.write(f"file '{video}'\n")
            output_video = os.path.join(target_dir, "FINAL_TRAILER_COLLECTION.mp4")
            cmd_merge = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "inputs.txt", "-c", "copy", "FINAL_TRAILER_COLLECTION.mp4", "-y"]
            try:
                subprocess.run(cmd_merge, cwd=target_dir, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                print(f"{GREEN_COLOR}[V] Merge completed: {output_video}{RESET}")
                if os.path.exists(list_path): os.remove(list_path)
            except Exception as e:
                print(f"{RED_COLOR}[X] FFmpeg Error: {e}{RESET}")
        else:
            print(f"{YELLOW_COLOR}[!] Insufficient trailers ({len(video_files)}) per il merge.{RESET}")
print(f"\n{RED_COLOR}*** TASK FINISHED ***{RESET}")
