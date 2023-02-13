from flask import Flask, render_template, session, request, redirect

import spotipy
from spotipy.oauth2 import SpotifyOAuth


app = Flask(__name__)
app.secret_key = "kaPL5tqKlx3TH_mVc83gR_TxV6XoV2"
SPOTIFY_CLIENT_ID="98b858202f174832885d46b4ab3433fb"
SPOTIFY_CLIENT_SECRET="9288bb7025134731a9fef97d0f2013d7"
SPOTIFY_REDIRECT_URI="http://127.0.0.1:5000"
SPOTIFY_SCOPES="user-library-read,playlist-modify-private,playlist-read-collaborative"
cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
auth_manager = spotipy.oauth2.SpotifyOAuth(scope=SPOTIFY_SCOPES,
                                           client_secret=SPOTIFY_CLIENT_SECRET,
                                           client_id=SPOTIFY_CLIENT_ID,
                                           cache_handler=cache_handler,
                                           redirect_uri=SPOTIFY_REDIRECT_URI,
                                           show_dialog=True)
sp = spotipy.Spotify(auth_manager=auth_manager)


@app.route('/')
def index():
    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        return redirect(auth_manager.get_authorize_url())

    playlists = sp.current_user_playlists()
    return render_template("playlists.html", playlists=playlists["items"])


@app.route('/playlist_from_playlist/<playlist_id>')
def playlist_from_playlist(playlist_id):
    playlist = sp.playlist(playlist_id)
    tracks = [itm["track"] for itm in playlist["tracks"]["items"]]
    audio_features = sp.audio_features([track["id"] for track in tracks])
    for i in range(len(tracks)):
        tracks[i]["af"] = audio_features[i]
    tracks.sort(reverse=True, key=lambda x: x["af"]["danceability"] + x['af']['energy'] + x['af']['valence'])
    return render_template("from_playlist.html", tracks=tracks)


if __name__ == '__main__':
    app.run(port=5050)
