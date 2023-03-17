# Spotify to YouTube Music Transfer Tool

This is a Python script that transfers your Spotify playlists, liked songs, and followed artists to YouTube Music.

## Prerequisites

-   Python 3.7 or higher
-   A Spotify Developer account, and an app created with access to your personal Spotify data. [Click here](https://developer.spotify.com/dashboard/applications) to create a new app or access an existing one.

## Installation and Usage

1. First, make sure you have the latest version of Python. [Follow these instructions](https://www.python.org/downloads/) to install Python if you haven't already.

2. Then, install the required dependencies using the following command:

`pip install spotipy ytmusicapi`

3. Download the script and run it by navigating to the directory where it is located and running the following command:

`python spotify_to_ytmusic.py`

### Setting up Spotify Authentication

4.  Go to the Spotify Developer Dashboard and create a new application or open an existing one.
5.  In your app settings, add `http://localhost/` as a Redirect URI.
6.  Paste the Client ID and Secret ID when prompted by the script.

### Setting up YouTube Music Authentication

7.  Follow the instructions at [https://ytmusicapi.readthedocs.io/en/stable/setup.html#copy-authentication-headers](https://ytmusicapi.readthedocs.io/en/stable/setup.html#copy-authentication-headers) to copy your authentication headers from your Youtube Music account.
8.  Paste the authentication headers when prompted by the script.

## Troubleshooting

YouTube Music limits you from creating too many playlists too quickly. If you have a lot of Spotify playlists, the script might fail partway through the process, outputting 'you are creating too many playlists' errors. If this happens, simply run the script again after some time has passed, and it will continue where it left off.

## Contributing

If you'd like to contribute to this project, please open an issue or submit a pull request with your proposed changes.

## License

This project is licensed under the GNU General Public License v3.0.
