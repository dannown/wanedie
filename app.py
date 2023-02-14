from flask import Flask, render_template, session, request, redirect, g, url_for

import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = "kaPL5tqKlx3TH_mVc83gR_TxV6XoV2"
SPOTIFY_CLIENT_ID = "98b858202f174832885d46b4ab3433fb"
SPOTIFY_CLIENT_SECRET = "9288bb7025134731a9fef97d0f2013d7"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5050"
SPOTIFY_SCOPES = ",".join([
    "user-library-read",
    "playlist-modify-private",
    "playlist-read-collaborative",
    "playlist-read-private",
    "playlist-modify-public"
])
cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
auth_manager = SpotifyOAuth(scope=SPOTIFY_SCOPES,
                            client_secret=SPOTIFY_CLIENT_SECRET,
                            client_id=SPOTIFY_CLIENT_ID,
                            cache_handler=cache_handler,
                            redirect_uri=SPOTIFY_REDIRECT_URI,
                            show_dialog=True)
sp = spotipy.Spotify(auth_manager=auth_manager)

SESSION_WORKING_PLAYLIST_ID = 'working_playlist_id'


@app.before_request
def check_auth_token():
    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        return redirect(auth_manager.get_authorize_url())


@app.before_request
def load_working_playlist():
    if SESSION_WORKING_PLAYLIST_ID in session:
        g.working_playlist = sp.playlist(session[SESSION_WORKING_PLAYLIST_ID])
        g.working_playlist_track_ids = [item['track']['id'] for item in g.working_playlist['tracks']['items']]
    else:
        g.pop("working_playlist", None)
        g.pop("working_playlist_track_ids", None)


@app.route('/select_playlist_for_from_playlist')
def select_playlist_for_from_playlist():
    playlists = sp.current_user_playlists()
    return render_template("select_playlist_for_from_playlist.html", playlists=playlists['items'])


@app.route('/')
def index():
    if SESSION_WORKING_PLAYLIST_ID in session:
        return edit_working_playlist()

    playlists = sp.current_user_playlists(limit=50)
    return render_template("select_working_playlist.html", playlists=playlists["items"])


def load_tracks(playlist):
    tracks = [itm["track"] for itm in playlist["tracks"]["items"]]
    audio_features = sp.audio_features([track["id"] for track in tracks])
    for i in range(len(tracks)):
        tracks[i]["af"] = audio_features[i]
        tracks[i]['in_working_playlist'] = 'working_playlist_track_ids' in g and \
                                           tracks[i]['id'] in g.working_playlist_track_ids
    tracks.sort(reverse=True, key=lambda x: x["af"]["danceability"] + x['af']['energy'] + x['af']['valence'])
    return tracks




@app.route('/remove_track_from_working_playlist/<track_id>')
def remove_track_from_working_playlist(track_id):
    sp.playlist_remove_all_occurrences_of_items(g.working_playlist["id"], ["spotify:track:" + track_id])
    return redirect("/")


@app.route('/new_playlist', methods=['GET', 'POST'])
def new_playlist():
    if request.method == 'POST':
        name = request.form["name"]
        user = sp.current_user()
        fresh_playlist = sp.user_playlist_create(user["id"], name)
        session[SESSION_WORKING_PLAYLIST_ID] = fresh_playlist["id"]
        return redirect('/')
    return render_template("new_playlist.html")
def edit_working_playlist():
    playlist = g.working_playlist
    tracks = load_tracks(playlist)
    return render_template("edit_playlist.html", playlist=playlist, tracks=tracks)


@app.route('/set_working_playlist/<playlist_id>')
def set_working_playlist(playlist_id):
    session[SESSION_WORKING_PLAYLIST_ID] = playlist_id
    return redirect('/')


@app.route('/playlist_from_playlist/<playlist_id>', methods=['GET', 'POST'])
def playlist_from_playlist(playlist_id):
    if request.method == 'POST':
        sp.playlist_add_items(g.working_playlist['id'], ["spotify:track:" + request.form['add_track_id']])
        redirect(url_for("playlist_from_playlist", playlist_id=playlist_id))
    playlist = sp.playlist(playlist_id)
    tracks = load_tracks(playlist)
    return render_template("from_playlist.html", tracks=tracks, playlist=playlist)


@app.route('/unset_working_playlist')
def unset_working_playlist():
    session.pop(SESSION_WORKING_PLAYLIST_ID)
    return redirect('/')


@app.route('/delete_playlist/<playlist_id>')
def delete_playlist(playlist_id):
    sp.current_user_unfollow_playlist(playlist_id)
    return redirect('/')


if __name__ == '__main__':
    app.run(port=5050)
