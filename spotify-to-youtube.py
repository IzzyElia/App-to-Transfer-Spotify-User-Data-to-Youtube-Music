# CONFIG --------------------------------------
SPOTIFY_AUTH_FILE = "spotify_auth.json"
YTMUSIC_HEADERS_FILE = 'ytmusic_headers_auth.json'
SPOTIFY_REDIRECT_URI = 'http://localhost/'
# ---------------------------------------------


import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ytmusicapi
import json


def setYTMusicAPI(use_existing_headers_file):
    if use_existing_headers_file:
        return ytmusicapi.YTMusic(YTMUSIC_HEADERS_FILE)
    else:
        user_headers = input("Paste your authentication headers here\n(follow the instructions at https://ytmusicapi.readthedocs.io/en/latest/setup.html under 'copy authentication headers', then paste those headers here): ")
        return ytmusicapi.YTMusic.setup(filepath=YTMUSIC_HEADERS_FILE, headers_raw=user_headers)

def load_spotify_auth_info(auth_file):
    if os.path.exists(auth_file):
        use_existing_auth = input("Use existing Spotify authentication info? (y/n): ")
        if use_existing_auth == 'y':
            with open(auth_file, 'r') as f:
                auth_info = json.load(f)
                return auth_info['client_id'], auth_info['client_secret']
    client_id = input("Copy the client id from your spotify app and paste it here: ")
    client_secret = input("Copy the client secret from your spotify app and paste it here: ")
    auth_info = {"client_id": client_id, "client_secret": client_secret}
    with open(auth_file, 'w') as f:
        json.dump(auth_info, f)
    return client_id, client_secret


def get_spotify_playlists(sp):
    username = sp.me()['id']
    playlists = []
    offset = 0
    while True:
        results = sp.user_playlists(sp.me()['id'], offset=offset)
        playlists.extend(results['items'])
        if results['next'] is None:
            break
        offset += len(results['items'])
    return playlists

def get_ytmusic_playlists(youtube_music):
    return youtube_music.get_library_playlists()

def verify_playlists(playlists, sp):
    for playlist in playlists:
        print(playlist['name'])
        results = sp.playlist_tracks(playlist['id'], limit=3)
        for track in results['items']:
            print(f" - {track['track']['name']}")
        if playlist['tracks']['total'] > 3:
            print (f" - plus {playlist['tracks']['total'] - 3} more tracks")
    print ("Does this look correct (y/n): ")
    return input() == 'y'

def get_playlist_tracks(playlist_id, sp):
    tracks = []
    offset = 0
    while True:
        results = sp.playlist_tracks(playlist_id, offset=offset)
        tracks.extend(results['items'])
        if results['next'] is None:
            break
        offset += len(results['items'])
    return tracks

def transfer_playlists_to_ytmusic(youtube_music, sp):
    spotify_playlists = get_spotify_playlists(sp)
    ytm_playlists = get_ytmusic_playlists(youtube_music)
    ytm_playlist_dict = {pl['title']: pl for pl in ytm_playlists}
    error_free = True

    # Calculate the total number of tracks across all playlists
    total_tracks = sum([playlist['tracks']['total'] for playlist in spotify_playlists])
    tracks_processed = 0

    for playlist in spotify_playlists:
        recreate_playlist = False
        if playlist['name'] in ytm_playlist_dict:
            ytm_playlist = ytm_playlist_dict[playlist['name']]
            #Compare the number of tracks in the spotify and youtube music playlists
            spotify_count = playlist['tracks']['total']
            youtube_music_count = int(ytm_playlist['count'])
            if spotify_count != youtube_music_count:
                print(f"{playlist['name']} exists on YouTube Music, but has a different track list. Recreating the playlist...")
                youtube_music.delete_playlist(ytm_playlist['playlistId'])
                recreate_playlist = True
            else:
                print(f"{playlist['name']} already exists on YouTube Music. Skipping...")
                continue
        else:
            print(f"{playlist['name']} does not exist on YouTube Music. Creating...")
            recreate_playlist = True

        if recreate_playlist:
            # Create a new playlist on YouTube Music
            try:
                ytm_playlist_id = youtube_music.create_playlist(playlist['name'], playlist['description'])
            except Exception as e:
                print(f"Could not create {playlist['name']} on YouTube Music (error: {e}). Skipping...")
                error_free = False
                continue

            # Retrieve the Spotify playlist tracks
            tracks = get_playlist_tracks(playlist['id'], sp)

            for track in tracks:
                track_info = track['track']
                search_query = f"{track_info['artists'][0]['name']} - {track_info['name']}"
                search_results = youtube_music.search(search_query, filter='songs')

                tracks_processed += 1
                percentage_completed = tracks_processed / total_tracks * 100

                print(f"Adding {search_query} to {playlist['name']} ({percentage_completed:.2f}% completed)...")

                if search_results:
                    song_id = search_results[0]['videoId']
                    try:
                        youtube_music.add_playlist_items(ytm_playlist_id, [song_id], duplicates=False)
                    except Exception as e:
                        print(f"Could not add {search_query} to {playlist['name']} on YouTube Music (error: {e}). Skipping...")
                        error_free = False
                        continue
                else:
                    print(f"Could not find {search_query} on YouTube Music")

    if error_free:
        print("All playlists successfully transferred from Spotify to YouTube Music!")
    else:
        print("Some playlists could not be transferred from Spotify to YouTube Music. This is probably because Youtube complained about you creating too many playlists to quickly. Try running the script again after some time has passed to continue the process")


def get_spotify_saved_tracks(sp):
    saved_tracks = []
    offset = 0
    while True:
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
        saved_tracks.extend(results['items'])
        if results['next'] is None:
            break
        offset += len(results['items'])
    return saved_tracks

def get_ytmusic_liked_songs(youtube_music):
    results = youtube_music.get_liked_songs(limit=None)['tracks']
    return results

def transfer_liked_songs_to_ytmusic(youtube_music, sp):
    print("Transferring liked songs from Spotify to YouTube Music...")
    saved_tracks = get_spotify_saved_tracks(sp)
    ytm_liked_songs = get_ytmusic_liked_songs(youtube_music)
    ytm_liked_song_names = []
    for song in ytm_liked_songs:
        ytm_liked_song_names.append(f"{song['artists'][0]['name']} - {song['title']}")

    total_saved_tracks = len(saved_tracks)
    for i, track_item in enumerate(saved_tracks, start=1):
        track = track_item['track']
        search_query = f"{track['artists'][0]['name']} - {track['name']}"
        search_results = youtube_music.search(search_query, filter='songs')
        progress_percentage = (i / total_saved_tracks) * 100
        print(f"\rProgress: {progress_percentage:.2f}%...", end="", flush=True)

        if search_results:
            song_name = f"{search_results[0]['artists'][0]['name']} - {search_results[0]['title']}"
            if song_name not in ytm_liked_song_names:
                youtube_music.rate_song(search_results[0]['videoId'], 'LIKE')
                ytm_liked_song_names.append(song_name)
                print(f"Added {song_name} to liked songs on YouTube Music")
            else:
                print(f"{song_name} already liked on YouTube Music")
        else:
            print(f"Could not find {search_query} on YouTube Music")

def get_spotify_followed_artists(sp):
    followed_artists = []
    after = None
    while True:
        results = sp.current_user_followed_artists(limit=50, after=after)
        followed_artists.extend(results['artists']['items'])
        if results['artists']['next'] is None:
            break
        after = results['artists']['items'][-1]['id']
    return followed_artists

def get_ytmusic_subscriptions(youtube_music):
    return youtube_music.get_library_subscriptions(limit=None)

def transfer_followed_artists_to_ytmusic(youtube_music, sp):
    print("Transferring followed artists from Spotify to YouTube Music...")
    followed_artists = get_spotify_followed_artists(sp)
    ytm_subscriptions = get_ytmusic_subscriptions(youtube_music)
    ytm_subscribed_channels = {sub['artist']: sub for sub in ytm_subscriptions}

    for artist in followed_artists:
        search_query = f"{artist['name']} - Topic"
        search_results = youtube_music.search(search_query, filter='artists')

        if search_results:
            channel = search_results[0]
            channel_title = channel['artist']

            if channel_title not in ytm_subscribed_channels:
                youtube_music.subscribe_artists([channel['browseId']])
                print(f"Subscribed to {channel_title} on YouTube Music")
            else:
                print(f"Already subscribed to {channel_title} on YouTube Music")
        else:
            print(f"Could not find YouTube channel for {artist['name']}")


def Run():
    print("Spotify to YouTube Music Transfer Tool")
    print("=====================================")
    print("First let's setup spotify")
    print("Go to https://developer.spotify.com/dashboard/applications and create a new application, or open an existing one")
    print(f"In your app, go to 'edit settings' and add {SPOTIFY_REDIRECT_URI} as a redirect URI")
    client_id, client_secret = load_spotify_auth_info(SPOTIFY_AUTH_FILE)
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope="playlist-read-private user-library-read user-follow-read"))
    # Check if the YTMusic headers file exists
    # If it does, ask the user if they want to use it or generate a new one
    ytm = None
    if os.path.exists(YTMUSIC_HEADERS_FILE):
        continue_with_existing_file = input("Use existing youtube music authentication info? (y/n): ")
        if continue_with_existing_file == 'y':
            ytm = setYTMusicAPI(True)
        else:
            ytm = setYTMusicAPI(False)
    else:
        ytm = setYTMusicAPI(False)

    # Check if both Spotify and YouTube Music authentications are correct
    try:
        username = sp.me()['id']
    except Exception as e:
        print(f"Spotify authentication failed: {e}")
        return

    try:
        ytm.get_library_songs(limit=1)
    except Exception as e:
        print(f"YouTube Music authentication failed: {e}")
        return


    while True:
        userInput = str.lower(input("Options: \n'transfer playlists' \n'transfer liked songs' \n'transfer followed artists' \n'transfer all' \n'exit' \n"))
        if userInput == "transfer playlists":
            transfer_playlists_to_ytmusic(ytm, sp)
            print( "Done!")
        elif userInput == "transfer liked songs":
            transfer_liked_songs_to_ytmusic(ytm, sp)
            print("Done!")
        elif userInput == "transfer followed artists":
            transfer_followed_artists_to_ytmusic(ytm, sp)
            print("Done!")
        elif userInput == "transfer all":
            transfer_playlists_to_ytmusic(ytm, sp)
            transfer_liked_songs_to_ytmusic(ytm, sp)
            transfer_followed_artists_to_ytmusic(ytm, sp)
            print ("Done!")
        elif userInput == "exit" or userInput == "quit" or userInput == "q":
            break
        elif userInput == "help":
            print("Options: \n'transfer playlists' \n'transfer liked songs' \n'transfer followed artists' \n'transfer all' \n'exit' \n")
        else:
            print("Invalid option")
    



Run()