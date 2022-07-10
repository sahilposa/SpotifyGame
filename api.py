"""Imports spotify python library"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import find_dotenv, load_dotenv


def authorization():
    """Gets authorization from API"""
    load_dotenv(find_dotenv())
    auth_manager = SpotifyClientCredentials()
    return spotipy.Spotify(auth_manager=auth_manager)


def search_genre(genre):
    """Search tracks in a genre"""
    spotify = authorization()
    uri_array = []
    results = spotify.search("genre:" + genre, 5)
    while len(uri_array) < 5:
        tracks = results["tracks"]
        items = tracks["items"]

        for track in items:
            url = track["preview_url"]
            uri = track["uri"]
            if url is not None:
                uri_array.append(uri)
            if len(uri_array) == 5:
                break
        results = spotify.next(tracks)

    return uri_array


def get_song_urls(song_arr):
    """Gets song urls"""
    url_arr = []
    if song_arr is None:
        return "Error: No Genre Chosen"
    spotify = authorization()
    results = spotify.tracks(song_arr)
    tracks = results["tracks"]
    for track in tracks:
        url = track["preview_url"]
        if url is None:
            url = "No Preview Available At This Time"
        url_arr.append(url)
    return url_arr


def get_song_titles(song_arr):
    """Gets song titles"""
    url_arr = []
    if song_arr is None:
        return "Error: No Genre Chosen"
    spotify = authorization()
    results = spotify.tracks(song_arr)
    tracks = results["tracks"]
    for track in tracks:
        url_arr.append(track["name"])
    return url_arr


def get_album_cover(song_arr):
    """Get album images"""
    img_arr = []
    if song_arr is None:
        return "Error: No Genre Chosen"
    spotify = authorization()
    results = spotify.tracks(song_arr)
    tracks = results["tracks"]
    for track in tracks:
        img_arr.append(track["album"]["images"][0]["url"])
    return img_arr


def get_artist(song_arr):
    """Get artist names"""
    artist_arr = []
    if song_arr is None:
        return "Error: No Genre Chosen"
    spotify = authorization()
    results = spotify.tracks(song_arr)
    tracks = results["tracks"]
    for track in tracks:
        artist_arr.append(track["artists"][0]["name"])
    return artist_arr
