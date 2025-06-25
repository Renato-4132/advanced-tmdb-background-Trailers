![Language](https://img.shields.io/badge/language-Python-F7DF1E?logo=python&logoColor=black) ![Repo Size](https://img.shields.io/github/repo-size/Renato-4132/advanced-tmdb-background) ![Windows Support](https://img.shields.io/badge/Windows-✔️-blue?logo=windows) ![macOS Support](https://img.shields.io/badge/macOS-✔️-lightgrey?logo=apple)
![Linux Support](https://img.shields.io/badge/Linux-✔️-yellow?logo=linux)

# Advanced TMDB Background

These are two simple scripts to retrieve TMDB  media background and use it as Wallpaper

You must open each .py file and add your TMDB API Read Access Token

"Authorization": "Bearer XXXXX" , where XXXXX is your API

Search TMDB movie or TV shows by ID and generate background graphics Ver.1.0.0

![Movie_output](https://github.com/user-attachments/assets/d12da655-d239-46e9-917d-f4f7d95f39cc)

**How to :**
- install latest version of python (https://www.python.org/downloads/)
- Install pip (follow the process here https://pip.pypa.io/en/stable/installation/)
- Download the content of this repository
- Go into the repository using a terminal and install dependencies :
  ```
  pip install -r requirements.txt
  ```
- Edit each python scripts with your info
- for TMDB create an account and get you api key here there https://www.themoviedb.org/settings/api
- As you run one of the script it will create a new folder and add the images automatically.
- Each time the scripts will run it will delete the content of the folder and create new images
- if you want to edit the overlay and background image I have included the source file as a vector format 


# TMDB.py

options:

  -h, --help           show this help message and exit
  
  -language            Language code for TMDB metadata type (default: it)
  
  -save-path           Directory where the output will be saved type (default: tmdb_backgrounds/)
  
  -gif-generate        Generate gifs y=generate (movie_id Scan Skipped)
  
  -dura                Timing between gif imagestype (default: 5000)-download-trailer    Download YouTube trailer for each movie/TV show
  
  -trailer-program     External program to use for downloading YouTube trailers (default: yt-dlp)
  
  -trailer-save-path   Directory to save downloaded trailers
  
  -default-browser     default browser for cookiestype (default: firefox)
  
  -merge-trailers      Merge all downloaded trailers into one file movie.mp4


usage: TMDB.py [-h] [-language ] [-save-path ] [-gif-gen ] [-dura ]..............


# TMDB-cli.py

options:

  -h, --help           show this help message and exit
  
  -language            Language code for TMDB metadata type (default: it)
  
  -save-path           Directory where the output will be saved type (default: tmdb_backgrounds/)
  
  -gif-generate        Generate gifs y=generate
  
  -dura                Timing between gif imagestype (default: 5000)
  
  -download-trailer    Download YouTube trailer for this movie/TV show
  
  -trailer-program     External program to use for downloading YouTube trailers (default: yt-dlp)
  
  -trailer-save-path   Directory to save downloaded trailers
  
  -default-browser     default browser for cookies (default: firefox)
  
  -merge-trailers      Merge all downloaded trailers into one file movie.mp4
  
  -movie-id MOVIE_ID   TMDB movie id to process
  
  -tv-id TV_ID         TMDB tv id to process

  
usage: TMDB.py [-h] [-language ] [-save-path ] [-gif-gen ] [-dura ]..................

# TMDB-gui.py

  - A nice Gui for the two main programs !
