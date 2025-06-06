import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, session, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Configuração do Spotify
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'https://localhost:8000/callback')

scope = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing"

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Spotify Music App</title></head>
    <body>
        <h1>Spotify Music App</h1>
        <a href="/login">Login com Spotify</a>
    </body>
    </html>
    ''')

@app.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope
    )
    
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    token_info = session.get('token_info')
    if not token_info:
        return redirect('/login')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # Buscar música atual
    current_track = sp.current_user_playing_track()
    
    # Buscar playlists do usuário
    playlists = sp.current_user_playlists(limit=10)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard - Spotify App</title></head>
    <body>
        <h1>Seu Dashboard Spotify</h1>
        
        <h2>Música Atual:</h2>
        {% if current_track %}
            <p>{{ current_track.item.name }} - {{ current_track.item.artists[0].name }}</p>
        {% else %}
            <p>Nenhuma música tocando</p>
        {% endif %}
        
        <h2>Suas Playlists:</h2>
        <ul>
        {% for playlist in playlists.items %}
            <li>{{ playlist.name }} ({{ playlist.tracks.total }} músicas)</li>
        {% endfor %}
        </ul>
        
        <a href="/search">Buscar Músicas</a>
    </body>
    </html>
    ''', current_track=current_track, playlists=playlists)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    
    if query:
        token_info = session.get('token_info')
        if token_info:
            sp = spotipy.Spotify(auth=token_info['access_token'])
            results = sp.search(q=query, type='track', limit=10)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Buscar - Spotify App</title></head>
    <body>
        <h1>Buscar Músicas</h1>
        
        <form method="GET">
            <input type="text" name="q" value="{{ query }}" placeholder="Digite o nome da música...">
            <button type="submit">Buscar</button>
        </form>
        
        {% if results %}
            <h2>Resultados:</h2>
            <ul>
            {% for track in results.tracks.items %}
                <li>{{ track.name }} - {{ track.artists[0].name }}</li>
            {% endfor %}
            </ul>
        {% endif %}
        
        <a href="/dashboard">Voltar ao Dashboard</a>
    </body>
    </html>
    ''', query=query, results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)