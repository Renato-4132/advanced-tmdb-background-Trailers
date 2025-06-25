#!/usr/bin/env python3

import argparse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import os
import shutil
from urllib.request import urlopen
import textwrap
from datetime import datetime, timedelta
import imageio
import sys
import subprocess
import glob
import time
import random

WHITE_COLOR = "\033[97m"
RED_COLOR = "\033[91m"
YELLOW_COLOR = "\033[93m"
RESET_COLOR = "\033[0m"

# Base URL for the API
url = "https://api.themoviedb.org/3/"

# Set your TMDB API Read Access Token key here
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmNzdhNzNlZjMzYzQyZWI4ZjdlYTQ1ODI4MzFkNDNhNyIsIm5iZiI6MTU4NTM4MDMzMy4zNTUsInN1YiI6IjVlN2VmYmVkYTQxMGM4MDAxODUyM2QxNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.qWXoGG-HJU9To7RV-HpCo9uCY7uFqW-fxPGQHP4hARI"
}

cookies = "--cookies-from-browser"

parser = argparse.ArgumentParser(description="Search Trending TMDB movies or TV shows and generate background graphics ver.1.0.0")
parser.add_argument('-language', metavar='', type=str, default="it", help="Language code for TMDB metadata " "type (default: %(default)s)")
parser.add_argument('-save-path', metavar='', type=str, default="tmdb_backgrounds/", help="Directory where the output will be saved " "type (default: %(default)s)")
parser.add_argument("-gif-generate", action='store_true', help="Generate gifs")
parser.add_argument("-dura", metavar='', type=int, default=5000, help="Timing between gif images" "type (default: %(default)s)")
parser.add_argument('-download-trailer', action='store_true', help="Download YouTube trailer for each movie/TV show")
parser.add_argument('-trailer-program', metavar='', type=str, default="yt-dlp", help="External program to use for downloading YouTube trailers (default: yt-dlp)")
parser.add_argument('-trailer-save-path', metavar='', type=str, default="tmdb_trailers/", help="Directory to save downloaded trailers")
parser.add_argument('-default-browser', metavar='', type=str, default="firefox", help="default browser for cookies" "type (default: %(default)s)")
parser.add_argument('-merge-trailers', action='store_true', help="Merge all downloaded trailers into one file movie.mp4")
args = parser.parse_args()
gif_generate = args.gif_generate

os.makedirs(args.save_path, exist_ok=True)

if args.download_trailer:
    if os.path.exists(args.trailer_save_path):
        shutil.rmtree(args.trailer_save_path)
    os.makedirs(args.trailer_save_path, exist_ok=True)

os.system('cls' if os.name == 'nt' else 'clear')
now = datetime.now()
print(f"{RED_COLOR}Date:{RESET_COLOR} {now.strftime('%Y-%m-%d')} {RED_COLOR}Time:{RESET_COLOR} {now.strftime('%H:%M:%S')}")
print(f"")
print(f"{WHITE_COLOR}-*-{RED_COLOR}Search Trending TMDB movies or TV shows and generate background gif{WHITE_COLOR}-*-{RESET_COLOR}")
print(f"")
print(f"{WHITE_COLOR}Selected language..........>:{RED_COLOR} {args.language}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected save-path.........>:{RED_COLOR} {args.save_path}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected gif-generate......>:{RED_COLOR} {args.gif_generate}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected download-trailer..>:{RED_COLOR} {args.download_trailer}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected trailer-save-path.>:{RED_COLOR} {args.trailer_save_path}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected trailer-program...>:{RED_COLOR} {args.trailer_program}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected default-browser...>:{RED_COLOR} {args.default_browser}{RESET_COLOR}")
print(f"{WHITE_COLOR}Selected merge trailers....>:{RED_COLOR} {args.merge_trailers}{RESET_COLOR}")
print(f"")

# TV Exclusion list - this filter will exclude Tv shows from chosen countries that have a specific genre
tv_excluded_countries=['XX','XX','XX'] #based on ISO 3166-1 alpha-2 codes, enter lowercase like ['cn','kr','jp','fr','us']
tv_excluded_genres=['XXXX'] # like ['Animation']

# Movie Exclusion list - this filter will exclude movies from chosen countries that have a specific genre
movie_excluded_countries=['XX','XX','XXX'] #based on ISO 3166-1 alpha-2 codes, enter lowercase like ['cn','kr','jp','fr','us']
movie_excluded_genres=['XXX'] # like ['Animation']

# Keyword exclusion list - this filter will exclude movies or tv shows that contain a specific keyword in their TMDB profile
excluded_keywords = ['XXX','XXX','XXX'] # like ['adult']

# Filter movies by release date and tv shows by last air date
max_air_date = datetime.now() - timedelta(days=30) #specify the number of days since the movei release or the tv show last air date, shows before this date will be excluded 

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


# Endpoint for trending shows
trending_movies_url = f'{url}trending/movie/week?language={args.language}'
trending_tvshows_url = f'{url}trending/tv/week?language={args.language}'

# Fetching trending movies
trending_movies_response = requests.get(trending_movies_url, headers=headers)
trending_movies = trending_movies_response.json()

# Fetching trending TV shows
trending_tvshows_response = requests.get(trending_tvshows_url, headers=headers)
trending_tvshows = trending_tvshows_response.json()

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

# Fetching TV show details
def get_tv_show_details(tv_id):
    tv_details_url = f'{url}tv/{tv_id}?language={args.language}'
    tv_details_response = requests.get(tv_details_url, headers=headers)
    return tv_details_response.json()

# Fetching movie details
def get_movie_details(movie_id):
    movie_details_url = f'{url}movie/{movie_id}?language={args.language}'
    movie_details_response = requests.get(movie_details_url, headers=headers)
    return movie_details_response.json()

# Function to fetch keywords for a movie
def get_movie_keywords(movie_id):
    keywords_url = f"{url}movie/{movie_id}/keywords"
    response = requests.get(keywords_url, headers=headers)
    if response.status_code == 200:
        return [keyword['name'].lower() for keyword in response.json().get('keywords', [])]
    return []

# Function to fetch keywords for a TV show
def get_tv_keywords(tv_id):
    keywords_url = f"{url}tv/{tv_id}/keywords"
    response = requests.get(keywords_url, headers=headers)
    if response.status_code == 200:
        return [keyword['name'].lower() for keyword in response.json().get('results', [])]
    return []

# Function to fetch trailer URL for a movie
def get_movie_trailer_url(movie_id):
    trailer_url = None
    videos_url = f"{url}movie/{movie_id}/videos?language={args.language}"
    response = requests.get(videos_url, headers=headers)
    if response.status_code == 200:
        results = response.json().get('results', [])
        for video in results:
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break
    return trailer_url

# Function to fetch trailer URL for a TV show
def get_tv_trailer_url(tv_id):
    trailer_url = None
    videos_url = f"{url}tv/{tv_id}/videos?language={args.language}"
    response = requests.get(videos_url, headers=headers)
    if response.status_code == 200:
        results = response.json().get('results', [])
        for video in results:
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break
    return trailer_url

if os.path.exists(args.save_path):
    shutil.rmtree(args.save_path)
os.makedirs(args.save_path, exist_ok=True)

#truncate overview
def truncate_overview(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars]
    else:
        return overview

#truncate
def truncate(overview, max_chars):
    if len(overview) > max_chars:
        return overview[:max_chars-3]
    else:
        return overview

# resize image
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
    resized_img = image.resize((new_width, new_height))
    return resized_img

def clean_filename(filename):
    cleaned_filename = "".join(c if c.isalnum() or c in "" else "" for c in filename)
    return cleaned_filename

# Fetch movie or TV show logo in English
def get_logo(media_type, media_id, language="en"):
    logo_url = f"{url}{media_type}/{media_id}/images?language=en"
    logo_response = requests.get(logo_url, headers=headers)
    if logo_response.status_code == 200:
        logos = logo_response.json().get("logos", [])
        for logo in logos:
            if logo.get("iso_639_1") == "en" and logo.get("file_path", "").endswith(".png"):
                return logo["file_path"]
    return None

def process_image(image_url, title, is_movie, genre, year, rating, duration=None, seasons=None):
    response = requests.get(image_url, timeout=10)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image = resize_image(image, 1500)
        # ---- Updated paths below ----
        image_base = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(image_base, "images")
        bckg = Image.open(os.path.join(images_dir, "bckg.png"))
        overlay = Image.open(os.path.join(images_dir, "overlay.png"))
        tmdblogo = Image.open(os.path.join(images_dir, "tmdblogo.png"))
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
        logo_path = get_logo("movie" if is_movie else "tv", movie['id'] if is_movie else tvshow['id'], language="en")
        logo_drawn = False
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

def should_exclude_movie(movie, movie_excluded_countries=movie_excluded_countries, movie_excluded_genres=movie_excluded_genres, excluded_keywords=excluded_keywords):
    country = movie.get('origin_country', '').lower()
    genres = [movie_genres.get(genre_id, '') for genre_id in movie.get('genre_ids', [])]
    movie_keywords = get_movie_keywords(movie['id']) if excluded_keywords else []
    release_date_str = movie.get('release_date')
    release_date = datetime.strptime(release_date_str, "%Y-%m-%d") if release_date_str else None
    if (country in movie_excluded_countries or 
        any(genre in movie_excluded_genres for genre in genres) or 
        any(keyword in movie_keywords for keyword in excluded_keywords) or
        (release_date and release_date < max_air_date)):
        return True
    return False

def should_exclude_tvshow(tvshow, tv_excluded_countries=tv_excluded_countries, tv_excluded_genres=tv_excluded_genres, excluded_keywords=excluded_keywords):
    country = tvshow.get('origin_country', [''])[0].lower()
    genres = [tv_genres.get(genre_id, '') for genre_id in tvshow.get('genre_ids', [])]
    tv_keywords = get_tv_keywords(tvshow['id']) if excluded_keywords else []
    last_air_date_str = get_tv_show_details(tvshow['id']).get('last_air_date')
    last_air_date = datetime.strptime(last_air_date_str, "%Y-%m-%d") if last_air_date_str else None
    if (country in tv_excluded_countries or 
        any(genre in tv_excluded_genres for genre in genres) or 
        any(keyword in tv_keywords for keyword in excluded_keywords) or
        (last_air_date and last_air_date < max_air_date)):
        return True
    return False

for movie in trending_movies.get('results', []):
    if should_exclude_movie(movie):
        continue
    title = movie['title']
    overview = movie['overview']
    if not overview:
        movie_details = get_movie_details(movie['id'])
        mv_id = movie_details.get('id', 0)
        print(f"{YELLOW_COLOR}No {args.language} plot found for {title}{RESET_COLOR}")
        print(f"{YELLOW_COLOR}https://www.themoviedb.org/movie/{mv_id}/edit{RESET_COLOR}")
        time.sleep(3)
        overview = "We do not have a translated description. Help us expand our database by adding one."
    year = movie['release_date']
    rating = round(movie['vote_average'],1)
    genre = ', '.join([movie_genres[genre_id] for genre_id in movie['genre_ids']])
    movie_details = get_movie_details(movie['id'])
    duration = movie_details.get('runtime', 0)
    if duration:
        hours = duration // 60
        minutes = duration % 60
        duration = f"{hours}h{minutes}min"
    else:
        duration = "N/A"
    backdrop_path = movie['backdrop_path']
    custom_text = "Now Trending on"
    if backdrop_path:
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        process_image(image_url, title, is_movie=True, genre=genre, year=year, rating=rating, duration=duration)
    else:
        print(f"{YELLOW_COLOR}No backdrop image found for {title}{RESET_COLOR}")
    trailer_url = get_movie_trailer_url(movie['id'])
    mv_id = movie_details.get('id', 0)
    if trailer_url:
        print(f"{YELLOW_COLOR}Trailer {WHITE_COLOR}{args.language}{YELLOW_COLOR} for {WHITE_COLOR}{mv_id} {RED_COLOR}{title}: {WHITE_COLOR}{trailer_url}{RESET_COLOR}")
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

for tvshow in trending_tvshows.get('results', []):
    if should_exclude_tvshow(tvshow):
        continue
    title = truncate_overview(tvshow['name'],38)
    overview = tvshow['overview']
    if not overview:
        tv_details = get_tv_show_details(tvshow['id'])
        tv_id = tv_details.get('id', 0)
        print(f"{YELLOW_COLOR}No {args.language} plot found for {title}{RESET_COLOR}")
        print(f"{YELLOW_COLOR}https://www.themoviedb.org/tv/{tv_id}/edit{RESET_COLOR}")
        overview = "We do not have a translated description. Help us expand our database by adding one."
    year = tvshow['first_air_date']
    rating = round(tvshow['vote_average'],1)
    genre = ', '.join([tv_genres[genre_id] for genre_id in tvshow['genre_ids']])
    tv_details = get_tv_show_details(tvshow['id'])
    seasons = tv_details.get('number_of_seasons', 0)
    backdrop_path = tvshow['backdrop_path']
    custom_text = "Now Trending on"
    if backdrop_path:
        image_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"
        process_image(image_url, title, is_movie=False, genre=genre, year=year, rating=rating, seasons=seasons)
    else:
        print(f"No backdrop image found for {title}")
    trailer_url = get_tv_trailer_url(tvshow['id'])
    tv_id = tv_details.get('id', 0)
    if trailer_url:
        print(f"{YELLOW_COLOR}Trailer {WHITE_COLOR}{args.language}{YELLOW_COLOR} for {WHITE_COLOR}{tv_id} {RED_COLOR}{title}: {WHITE_COLOR}{trailer_url}{RESET_COLOR}")
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

if args.gif_generate:
    os.system('cls' if os.name == 'nt' else 'clear')
    now = datetime.now()
    print(f"{RED_COLOR}Date:{RESET_COLOR} {now.strftime('%Y-%m-%d')} {RED_COLOR}Time:{RESET_COLOR} {now.strftime('%H:%M:%S')}")
    print(f"")
    print(f"{WHITE_COLOR}-*-{RED_COLOR}Search Trending TMDB movies or TV shows and generate background gif{WHITE_COLOR}-*-{RESET_COLOR}")
    print(f"")
    output_name_gif = "Movie_output.gif"
    output_gif = os.path.join(args.save_path, output_name_gif)
    print(f"{WHITE_COLOR}Converting files to gif..>: {RED_COLOR} {output_gif}{RESET_COLOR}")
    print(f"{WHITE_COLOR}Timing gifs..............>: {RED_COLOR} {args.dura}{RESET_COLOR}")
    image_files = sorted([os.path.join(args.save_path, file)
                     for file in os.listdir(args.save_path)
                     if file.endswith('.png') or file.endswith('.jpg')])
    with imageio.get_writer(output_gif, mode='I', duration=args.dura/1000.0) as writer:
        for filename in image_files:
            image = imageio.v3.imread(filename)
            writer.append_data(image)
    print(f"{WHITE_COLOR}GIF saved as.............>: {RED_COLOR} {output_gif}{RESET_COLOR}")
    print(f"")

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


