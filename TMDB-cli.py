#!/usr/bin/env python3

import argparse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import os
import shutil
import textwrap
from datetime import datetime, timedelta
import imageio
import sys
import subprocess
import time
import random

WHITE_COLOR = "\033[97m"
RED_COLOR = "\033[91m"
YELLOW_COLOR = "\033[93m"
RESET_COLOR = "\033[0m"

url = "https://api.themoviedb.org/3/"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmNzdhNzNlZjMzYzQyZWI4ZjdlYTQ1ODI4MzFkNDNhNyIsIm5iZiI6MTU4NTM4MDMzMy4zNTUsInN1YiI6IjVlN2VmYmVkYTQxMGM4MDAxODUyM2QxNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.qWXoGG-HJU9To7RV-HpCo9uCY7uFqW-fxPGQHP4hARI"
}

cookies = "--cookies-from-browser"


parser = argparse.ArgumentParser(description="Generate TMDB background graphics from a single movie or TV show ID")
parser.add_argument('-language', metavar='', type=str, default="it", help="Language code for TMDB metadata (default: %(default)s)")
parser.add_argument('-save-path', metavar='', type=str, default="tmdb_backgrounds/", help="Directory where the output will be saved (default: %(default)s)")
parser.add_argument("-gif-generate", action='store_true', help="Generate gifs")
parser.add_argument("-dura", metavar='', type=int,default=5000, help="Timing between gif images (default: %(default)s)")
parser.add_argument('-download-trailer', action='store_true', help="Download YouTube trailer for this movie/TV show")
parser.add_argument('-trailer-program', metavar='', type=str, default="yt-dlp", help="External program to use for downloading YouTube trailers (default: yt-dlp)")
parser.add_argument('-trailer-save-path', metavar='', type=str, default="tmdb_trailers/", help="Directory to save downloaded trailers")
parser.add_argument('-default-browser', metavar='', type=str, default="firefox", help="default browser for cookies (default: %(default)s)")
parser.add_argument('-merge-trailers', action='store_true', help="Merge all downloaded trailers into one file movie.mp4")
parser.add_argument('-movie-id', type=int, default=None, help="TMDB movie id to process ")
parser.add_argument('-tv-id', type=int, default=None, help="TMDB tv id to process ")
args = parser.parse_args()
gif_generate = {args.gif_generate}

os.makedirs(args.save_path, exist_ok=True)
os.makedirs(args.trailer_save_path, exist_ok=True)

os.system('cls' if os.name == 'nt' else 'clear')
now = datetime.now()
print(f"{RED_COLOR}Date:{RESET_COLOR} {now.strftime('%Y-%m-%d')} {RED_COLOR}Time:{RESET_COLOR} {now.strftime('%H:%M:%S')}")
print(f"")
print(f"{WHITE_COLOR}-*-{RED_COLOR}TMDB single movie/tv by ID background generator{WHITE_COLOR}-*-{RESET_COLOR}")
print(f"")
print(f"{WHITE_COLOR}Selected language..........>:{RED_COLOR} {args.language}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected save-path.........>:{RED_COLOR} {args.save_path}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected gif-generate......>:{RED_COLOR} {args.gif_generate}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected download-trailer..>:{RED_COLOR} {args.download_trailer}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected trailer-save-path.>:{RED_COLOR} {args.trailer_save_path}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected trailer-program...>:{RED_COLOR} {args.trailer_program}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected youtube-cookies...>:{RED_COLOR} {cookies}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected default-browser...>:{RED_COLOR} {args.default_browser}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected merge trailers....>:{RED_COLOR} {args.merge_trailers}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected movie id..........>:{RED_COLOR} {args.movie_id}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected tv id.............>:{RED_COLOR} {args.tv_id}{RESET_COLOR}")
print(f"")

# Save font locally
fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
os.makedirs(fonts_dir, exist_ok=True)
truetype_path = os.path.join(fonts_dir, "Roboto-Light.ttf")
truetype_url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf'

if not os.path.exists(truetype_path):
    try:
        response = requests.get(truetype_url, timeout=10)
        if response.status_code == 200:
            with open(truetype_path, 'wb') as f:
                f.write(response.content)
            print("Roboto-Light font saved")
        else:
            print(f"Failed to download Roboto-Light font. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while downloading the Roboto-Light font: {e}")

# Fetching genres for movies
genres_url = f'{url}genre/movie/list?language={args.language}'
genres_response = requests.get(genres_url, headers=headers)
genres_data = genres_response.json()
movie_genres = {genre['id']: genre['name'] for genre in genres_data.get('genres', [])}
# Fetching genres for TV shows
genres_url = f'{url}genre/tv/list?language={args.language}'
genres_response = requests.get(genres_url, headers=headers)
genres_data = genres_response.json()
tv_genres = {genre['id']: genre['name'] for genre in genres_data.get('genres', [])}

def get_movie_details(movie_id):
    movie_details_url = f'{url}movie/{movie_id}?language={args.language}'
    movie_details_response = requests.get(movie_details_url, headers=headers)
    return movie_details_response.json()
def get_tv_details(tv_id):
    tv_details_url = f'{url}tv/{tv_id}?language={args.language}'
    tv_details_response = requests.get(tv_details_url, headers=headers)
    return tv_details_response.json()
def get_movie_trailer_url(movie_id):
    trailer_url = None
    videos_url = f"{url}movie/{movie_id}/videos?language={args.language}"
    response = requests.get(videos_url, headers=headers)
    if response.status_code == 200:
        for video in response.json().get('results', []):
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break
    return trailer_url
def get_tv_trailer_url(tv_id):
    trailer_url = None
    videos_url = f"{url}tv/{tv_id}/videos?language={args.language}"
    response = requests.get(videos_url, headers=headers)
    if response.status_code == 200:
        for video in response.json().get('results', []):
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break
    return trailer_url
def get_logo(media_type, media_id, language="en"):
    logo_url = f"{url}{media_type}/{media_id}/images?language=en"
    logo_response = requests.get(logo_url, headers=headers)
    if logo_response.status_code == 200:
        for logo in logo_response.json().get("logos", []):
            if logo["iso_639_1"] == "en" and logo["file_path"].endswith(".png"):
                return logo["file_path"]
    return None
def truncate(s, max_chars):
    return s[:max_chars-3] if len(s) > max_chars else s

def resize_image(image, height):
    ratio = height / image.height
    width = int(image.width * ratio)
    return image.resize((width, height))
def resize_logo(image, width, height):
    aspect_ratio = image.width / image.height
    new_width = width
    new_height = int(new_width / aspect_ratio)
    if new_height > height:
        new_height = height
        new_width = int(new_height * aspect_ratio)
    return image.resize((new_width, new_height))
def clean_filename(filename):
    return "".join(c if c.isalnum() else "" for c in filename)

def process_image(image_url, title, is_movie, genre, year, rating, duration=None, seasons=None):
    response = requests.get(image_url, timeout=10)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image = resize_image(image, 1500)
        bckg = Image.open(os.path.join(os.path.dirname(__file__), "images/", "bckg.png"))
        overlay = Image.open(os.path.join(os.path.dirname(__file__), "images/", "overlay.png"))
        tmdblogo = Image.open(os.path.join(os.path.dirname(__file__), "images/", "tmdblogo.png"))
        bckg.paste(image, (1175, 0))
        bckg.paste(overlay, (1175, 0), overlay)
        bckg.paste(tmdblogo, (680, 1115), tmdblogo)
        draw = ImageDraw.Draw(bckg)
        font_title = ImageFont.truetype(truetype_path, size=190)
        font_overview = ImageFont.truetype(truetype_path, size=50)
        font_custom = ImageFont.truetype(truetype_path, size=60)
        shadow_color = "black"
        main_color = "white"
        overview_color = (150, 150, 150)
        metadata_color = "white"
        title_position = (200, 420)
        overview_position = (210, 730)
        shadow_offset = 2
        info_position = (210, 650)
        custom_position = (210, 1100)
        wrapped_overview = "\n".join(textwrap.wrap(overview, width=70, max_lines=6, placeholder=" ..."))
        draw.text((overview_position[0] + shadow_offset, overview_position[1] + shadow_offset), wrapped_overview, font=font_overview, fill=shadow_color)
        draw.text(overview_position, wrapped_overview, font=font_overview, fill=metadata_color)
        if is_movie:
            genre_text = genre
            additional_info = f"{duration}"
        else:
            genre_text = genre
            additional_info = f"{seasons} {'Season' if seasons == 1 else 'Seasons'}"
        rating_text = "TMDB: " + str(rating)
        year_text = truncate(str(year), 7)
        info_text = f"{genre_text}  \u2022  {year_text}  \u2022  {additional_info}  \u2022  {rating_text}"
        draw.text((info_position[0] + shadow_offset, info_position[1] + shadow_offset), info_text, font=font_overview, fill=shadow_color)
        draw.text(info_position, info_text, font=font_overview, fill=overview_color)
        logo_drawn = False
        logo_path = get_logo("movie" if is_movie else "tv", args.movie_id if is_movie else args.tv_id, language="en")
        if logo_path:
            logo_url = f"https://image.tmdb.org/t/p/original{logo_path}"
            logo_response = requests.get(logo_url)
            if logo_response.status_code == 200:
                try:
                    logo_image = Image.open(BytesIO(logo_response.content))
                    logo_image = resize_logo(logo_image, 1000, 500)
                    logo_position = (210, info_position[1] - logo_image.height - 25)
                    logo_image = logo_image.convert('RGBA')
                    bckg.paste(logo_image, logo_position, logo_image)
                    logo_drawn = True
                except Exception as e:
                    print(f"Failed to draw logo for {title}: {e}")
        if not logo_drawn:
            draw.text((title_position[0] + shadow_offset, title_position[1] + shadow_offset), title, font=font_title, fill=shadow_color)
            draw.text(title_position, title, font=font_title, fill=main_color)
        custom_text = "Not Trending on"
        draw.text((custom_position[0] + shadow_offset, custom_position[1] + shadow_offset), custom_text, font=font_custom, fill=shadow_color)
        draw.text(custom_position, custom_text, font=font_custom, fill=metadata_color)
        filename = os.path.join(args.save_path, f"{clean_filename(title)}.jpg")
        bckg = bckg.convert('RGB')
        bckg.save(filename)
        os.system('cls' if os.name == 'nt' else 'clear')
        now = datetime.now()
        print(f"{RED_COLOR}Date:{RESET_COLOR} {now.strftime('%Y-%m-%d')} {RED_COLOR}Time:{RESET_COLOR} {now.strftime('%H:%M:%S')}")
        print(f"")
        print(f"{WHITE_COLOR}Image saved: {RED_COLOR}{filename}{RESET_COLOR}")
    else:
        print(f"Failed to download background for {title}")

if args.movie_id:
    movie = get_movie_details(args.movie_id)
    if "status_code" in movie:
        print(f"{RED_COLOR}Movie ID {args.movie_id} not found!{RESET_COLOR}")
        sys.exit(1)
    title = movie.get('title', 'Untitled')
    overview = movie.get('overview', '')
    if not overview:
        print(f"{YELLOW_COLOR}No {args.language} plot found for {title}{RESET_COLOR}")
        print(f"{YELLOW_COLOR}https://www.themoviedb.org/movie/{args.movie_id}/edit{RESET_COLOR}")
        time.sleep(3)
        overview = "We do not have a translated description. Help us expand our database by adding one."
    year = movie.get('release_date', 'N/A')
    rating = round(movie.get('vote_average', 0), 1)
    genre = ', '.join([movie_genres.get(g['id'], '') for g in movie.get('genres', [])])
    duration = movie.get('runtime', 0)
    if duration:
        hours = duration // 60
        minutes = duration % 60
        duration = f"{hours}h{minutes}min"
    else:
        duration = "N/A"
    backdrop_path = movie.get('backdrop_path')
    if backdrop_path:
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        process_image(image_url, title, is_movie=True, genre=genre, year=year, rating=rating, duration=duration)
    else:
        print(f"{YELLOW_COLOR}No backdrop image found for {title}{RESET_COLOR}")
    trailer_url = get_movie_trailer_url(args.movie_id)
    if trailer_url:
        print(f"{YELLOW_COLOR}Trailer {WHITE_COLOR}{args.language}{YELLOW_COLOR} for {WHITE_COLOR}{args.movie_id} {RED_COLOR}{title}: {WHITE_COLOR}{trailer_url}{RESET_COLOR}")
    else:
        print(f"{YELLOW_COLOR}No {args.language} trailer found for {title}{RESET_COLOR}")
    if args.download_trailer and trailer_url:
        trailer_filename = os.path.join(args.trailer_save_path, f"{clean_filename(title)}.mp4")
        cmd = [args.trailer_program, cookies, args.default_browser, trailer_url, "-o", trailer_filename]
        try:
            print(f"{WHITE_COLOR}Downloading trailer for {title} ...{RESET_COLOR}")
            subprocess.run(cmd, check=True)
            print(f"{WHITE_COLOR}Trailer saved to {trailer_filename}{RESET_COLOR}")
        except Exception as e:
            print(f"{YELLOW_COLOR}Failed to download {WHITE_COLOR}{args.language}{YELLOW_COLOR} trailer for {title}{RESET_COLOR}")

elif args.tv_id:
    tv = get_tv_details(args.tv_id)
    if "status_code" in tv:
        print(f"{RED_COLOR}TV ID {args.tv_id} not found!{RESET_COLOR}")
        sys.exit(1)
    title = tv.get('name', 'Untitled')
    overview = tv.get('overview', '')
    if not overview:
        print(f"{YELLOW_COLOR}No {args.language} plot found for {title}{RESET_COLOR}")
        print(f"{YELLOW_COLOR}https://www.themoviedb.org/tv/{args.tv_id}/edit{RESET_COLOR}")
        overview = "We do not have a translated description. Help us expand our database by adding one."
    year = tv.get('first_air_date', 'N/A')
    rating = round(tv.get('vote_average', 0), 1)
    genre = ', '.join([tv_genres.get(g['id'], '') for g in tv.get('genres', [])])
    seasons = tv.get('number_of_seasons', 0)
    backdrop_path = tv.get('backdrop_path')
    if backdrop_path:
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        process_image(image_url, title, is_movie=False, genre=genre, year=year, rating=rating, seasons=seasons)
    else:
        print(f"{YELLOW_COLOR}No backdrop image found for {title}{RESET_COLOR}")
    trailer_url = get_tv_trailer_url(args.tv_id)
    if trailer_url:
        print(f"{YELLOW_COLOR}Trailer {WHITE_COLOR}{args.language}{YELLOW_COLOR} for {WHITE_COLOR}{args.tv_id} {RED_COLOR}{title}: {WHITE_COLOR}{trailer_url}{RESET_COLOR}")
    else:
        print(f"{YELLOW_COLOR}No {args.language} trailer found for {title}{RESET_COLOR}")
    if args.download_trailer and trailer_url:
        trailer_filename = os.path.join(args.trailer_save_path, f"{clean_filename(title)}.mp4")
        cmd = [args.trailer_program, cookies, args.default_browser, trailer_url, "-o", trailer_filename]
        try:
            print(f"{WHITE_COLOR}Downloading trailer for {title} ...{RESET_COLOR}")
            subprocess.run(cmd, check=True)
            print(f"{WHITE_COLOR}Trailer saved to {trailer_filename}{RESET_COLOR}")
        except Exception as e:
            print(f"{YELLOW_COLOR}Failed to download {WHITE_COLOR}{args.language}{YELLOW_COLOR} trailer for {title}{RESET_COLOR}")

#else:
#    print(f"{RED_COLOR}Please specify either --movie-id or --tv-id!{RESET_COLOR}")
#    sys.exit(1)

if args.gif_generate:
    os.system('cls' if os.name == 'nt' else 'clear')
    now = datetime.now()
    print(f"{RED_COLOR}Date:{RESET_COLOR} {now.strftime('%Y-%m-%d')} {RED_COLOR}Time:{RESET_COLOR} {now.strftime('%H:%M:%S')}")
    print(f"")
    print(f"{WHITE_COLOR}-*-{RED_COLOR}TMDB background gif generator{WHITE_COLOR}-*-{RESET_COLOR}")
    print(f"")
    output_name_gif = "Movie_output.gif"
    output_gif = args.save_path + output_name_gif
    print(f"{WHITE_COLOR}Converting files to gif..>: {RED_COLOR} {output_gif}{RESET_COLOR}")
    print(f"{WHITE_COLOR}Timing gifs..............>: {RED_COLOR} {args.dura}{RESET_COLOR}")
    image_files = sorted([os.path.join(args.save_path, file)
        for file in os.listdir(args.save_path)
        if file.endswith('.png') or file.endswith('.jpg')])
    with imageio.get_writer(output_gif, mode='I', duration=args.dura) as writer:
        for filename in image_files:
            image = imageio.v3.imread(filename)
            writer.append_data(image)
    print(f"{WHITE_COLOR}GIF saved as.............>: {RED_COLOR} {output_gif}{RESET_COLOR}")
    print(f" ")
    
# GIF and merge logic as in your original code, but now only for generated files
if args.merge_trailers:
    video_exts = ('.mp4', '.mov', '.mkv', '.avi', '.webm')
    video_files = [
        f for f in os.listdir(args.trailer_save_path)
        if f.lower().endswith(video_exts)
    ]
    if video_files:
        random.shuffle(video_files)
        output_file = os.path.join(args.trailer_save_path, "movie.mkv")
        input_args = []
        filter_inputs = []
        for idx, vfile in enumerate(video_files):
            abspath = os.path.abspath(os.path.join(args.trailer_save_path, vfile))
            input_args += ['-i', abspath]
            filter_inputs.append(f'[{idx}:v:0][{idx}:a:0]')
        filter_complex = f"{''.join(filter_inputs)}concat=n={len(video_files)}:v=1:a=1[v][a]"
        cmd = [
            "ffmpeg",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-y",
            output_file
        ]
        print(f"{YELLOW_COLOR}Merging (shuffled) trailers into {output_file}{RESET_COLOR}")
        start_time = time.time()
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start_time
        print(f"{WHITE_COLOR}All trailers merged into {output_file}{RESET_COLOR}")
        print(f"{WHITE_COLOR}Time to finish job: {elapsed:.2f} seconds{RESET_COLOR}")
    else:
        print(f"{YELLOW_COLOR}No video files found in {args.trailer_save_path} to merge!{RESET_COLOR}")


