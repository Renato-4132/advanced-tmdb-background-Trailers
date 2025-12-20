![Language](https://img.shields.io/badge/language-Python-F7DF1E?logo=python&logoColor=black) ![Repo Size](https://img.shields.io/github/repo-size/Renato-4132/advanced-tmdb-background) ![Windows Support](https://img.shields.io/badge/Windows-✔️-blue?logo=windows) ![macOS Support](https://img.shields.io/badge/macOS-✔️-lightgrey?logo=apple)
![Linux Support](https://img.shields.io/badge/Linux-✔️-yellow?logo=linux)

# Advanced TMDB Background

![Schermata del 2025-12-20 09-13-32](https://github.com/user-attachments/assets/afb75224-8e5c-412d-93e2-a41d072e63f3)

These are two simple scripts to retrieve TMDB  media background and use it as Wallpaper

![Movie_output](https://github.com/user-attachments/assets/d12da655-d239-46e9-917d-f4f7d95f39cc)

**How to :**
- install latest version of python (https://www.python.org/downloads/)
- Install pip (follow the process here https://pip.pypa.io/en/stable/installation/)
- Download the content of this repository
- for TMDB create an account and get you api key here there https://www.themoviedb.org/settings/api
- As you run one of the script it will create a new folder and add the images automatically.

# TMDB.py

options:

-h, --help	Show the help message and exit.	

--api-url	The TMDB API base URL.	https://api.themoviedb.org/3

--api-auth	Your TMDB API Read Access Token (Bearer).	

--language	Language code for TMDB metadata (e.g., en, it, es).

--save-path	Directory where the generated backgrounds will be saved.

--movie-id	Specific TMDB Movie ID to process.

--tv-id	Specific TMDB TV Show ID to process.

--gif-generate	Enable GIF generation (skips static scan if movie_id is used).

--dura	Duration in milliseconds between GIF frames.

--download-trailer	Download the YouTube trailer for the media.

--merge-trailers	Merge all downloaded clips into a single movie.mp4.

--trailer-save-path	Directory where trailers will be stored.

--trailer-program	External downloTMDB.py --language en --limit 5ader to use (e.g., yt-dlp).

--default-browser	Browser to use for cookies during video extraction.	

--limit	Number of trending items to process if no ID is specified.


usage: TMDB.py [-h] [--api-url API_URL] [--api-auth API_AUTH] [--language LANGUAGE] [--save-path SAVE_PATH] [--movie-id MOVIE_ID]
               [--tv-id TV_ID] [--gif-generate] [--dura DURA] [--download-trailer] [--merge-trailers]
               [--trailer-save-path TRAILER_SAVE_PATH] [--trailer-program TRAILER_PROGRAM] [--default-browser DEFAULT_BROWSER]
               [--limit LIMIT]

example:
TMDB.py --language en --limit 5
Will generate backgrounds for the top 5 trending movies in English

# TMDB-gui.py

  - A nice Gui for the two main programs !
