import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, session, render_template_string, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Configuração do Spotify
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'https://d012-186-224-132-223.ngrok-free.app')

# Scopes necessários
scope = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing,playlist-read-private,user-read-recently-played,user-top-read"

def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope,
        show_dialog=True
    )

def get_spotify_client():
    token_info = session.get('token_info')
    if not token_info:
        return None
    return spotipy.Spotify(auth=token_info['access_token'])

def check_premium(sp):
    """Verifica se o usuário tem Spotify Premium"""
    try:
        user = sp.current_user()
        return user.get('product') == 'premium'
    except:
        return False

@app.route('/')
def index():
    code = request.args.get('code')
    if code:
        return redirect(f'/callback?code={code}')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spotify Music App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #191414; color: white; text-align: center; }
            .btn { background: #1db954; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 18px; }
            .btn:hover { background: #1ed760; }
            h1 { color: #1db954; font-size: 3em; margin-bottom: 20px; }
            .subtitle { color: #b3b3b3; font-size: 1.2em; margin-bottom: 40px; }
            .features { text-align: left; max-width: 600px; margin: 40px auto; }
            .feature { margin: 15px 0; padding: 10px; background: #282828; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🎵 Spotify Music Controller</h1>
        <p class="subtitle">Explore e controle sua música!</p>
        
        <div class="features">
            <div class="feature">🎧 <strong>Visualizar</strong> música atual e histórico</div>
            <div class="feature">🔍 <strong>Buscar</strong> músicas, artistas e álbuns</div>
            <div class="feature">🏆 <strong>Ver</strong> suas top músicas e artistas</div>
            <div class="feature">📊 <strong>Analisar</strong> seus hábitos musicais</div>
            <div class="feature">🎮 <strong>Controlar</strong> reprodução (Premium)</div>
        </div>
        
        <a href="/login" class="btn">🎧 Conectar ao Spotify</a>
    </body>
    </html>
    ''')

@app.route('/login')
def login():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = get_spotify_oauth()
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return f"Erro na autorização: {error}"
    if not code:
        return "Código de autorização não encontrado"
    
    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        session['token_info'] = token_info
        return redirect('/dashboard')
    except Exception as e:
        return f"Erro ao obter token: {e}"

@app.route('/dashboard')
def dashboard():
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    
    try:
        current_track = sp.current_user_playing_track()
        user_profile = sp.current_user()
        devices = sp.devices()
        is_premium = check_premium(sp)
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Spotify Controller</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #191414; color: white; }
                .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
                .player-card { background: linear-gradient(135deg, #1db954, #1ed760); padding: 30px; border-radius: 15px; margin: 20px 0; text-align: center; }
                .controls { display: flex; justify-content: center; gap: 15px; margin: 20px 0; }
                .control-btn { background: rgba(255,255,255,0.2); border: none; color: white; padding: 15px; border-radius: 50%; cursor: pointer; font-size: 20px; transition: all 0.3s; }
                .control-btn:hover { background: rgba(255,255,255,0.3); transform: scale(1.1); }
                .control-btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .play-pause { background: #fff; color: #1db954; font-size: 24px; padding: 20px; }
                .track-info { margin: 20px 0; }
                .track-title { font-size: 24px; font-weight: bold; margin: 10px 0; }
                .track-artist { font-size: 18px; opacity: 0.9; }
                .btn { background: #1db954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; display: inline-block; }
                .btn:hover { background: #1ed760; }
                .card { background: #282828; padding: 20px; margin: 20px 0; border-radius: 10px; }
                h1 { color: #1db954; text-align: center; }
                .premium-badge { background: #ffd700; color: #000; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
                .free-badge { background: #666; color: #fff; padding: 5px 10px; border-radius: 15px; font-size: 12px; }
                .warning { background: #ff6b35; color: white; padding: 15px; border-radius: 8px; margin: 10px 0; }
                .spotify-link { background: #1db954; color: white; padding: 8px 15px; text-decoration: none; border-radius: 20px; font-size: 14px; }
                .track-details { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; margin: 15px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎵 Olá, {{ user_name }}! 
                    {% if is_premium %}
                        <span class="premium-badge">PREMIUM</span>
                    {% else %}
                        <span class="free-badge">FREE</span>
                    {% endif %}
                </h1>
                
                <div class="player-card">
                    <div class="track-info">
                        {% if current_track and current_track.item %}
                            <div class="track-title">{{ current_track.item.name }}</div>
                            <div class="track-artist">{{ current_track.item.artists[0].name }}</div>
                            
                            <div class="track-details">
                                <div>💿 <strong>Álbum:</strong> {{ current_track.item.album.name }}</div>
                                <div>📅 <strong>Lançamento:</strong> {{ current_track.item.album.release_date }}</div>
                                <div>⭐ <strong>Popularidade:</strong> {{ current_track.item.popularity }}/100</div>
                                <div>⏱️ <strong>Duração:</strong> {{ (current_track.item.duration_ms // 60000) }}:{{ '%02d'|format((current_track.item.duration_ms % 60000) // 1000) }}</div>
                            </div>
                            
                            <div style="margin: 10px 0;">
                                <span style="background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 15px;">
                                    {{ "▶️ Tocando" if current_track.is_playing else "⏸️ Pausado" }}
                                </span>
                            </div>
                            
                            <a href="{{ current_track.item.external_urls.spotify }}" target="_blank" class="spotify-link">
                                🎧 Abrir no Spotify
                            </a>
                        {% else %}
                            <div class="track-title">Nenhuma música tocando</div>
                            <div class="track-artist">Abra o Spotify e comece a tocar algo!</div>
                        {% endif %}
                    </div>
                    
                    {% if not is_premium %}
                    <div class="warning">
                        ⚠️ <strong>Controles de reprodução requerem Spotify Premium</strong><br>
                        <small>Você pode visualizar informações e usar outras funcionalidades</small>
                    </div>
                    {% endif %}
                    
                    <div class="controls">
                        <button class="control-btn" onclick="previousTrack()" {{ "disabled" if not is_premium }}>⏮️</button>
                        <button class="control-btn play-pause" onclick="togglePlayPause()" {{ "disabled" if not is_premium }}>
                            {{ "⏸️" if current_track and current_track.is_playing else "▶️" }}
                        </button>
                        <button class="control-btn" onclick="nextTrack()" {{ "disabled" if not is_premium }}>⏭️</button>
                    </div>
                    
                    {% if current_track and current_track.item %}
                    <div style="margin-top: 20px;">
                        <button class="btn" onclick="showLyrics('{{ current_track.item.name }}', '{{ current_track.item.artists[0].name }}')">
                            📝 Ver Letra
                        </button>
                        <button class="btn" onclick="shareTrack('{{ current_track.item.external_urls.spotify }}', '{{ current_track.item.name }}', '{{ current_track.item.artists[0].name }}')" style="background: #3b82f6;">
                            📤 Compartilhar
                        </button>
                    </div>
                    {% endif %}
                </div>
                
                {% if devices and devices.devices %}
                <div class="card">
                    <h3>🔊 Dispositivos Spotify:</h3>
                    {% for device in devices.devices %}
                        <div style="background: #333; padding: 10px; border-radius: 5px; margin: 10px 0;">
                            <strong>{{ device.name }}</strong> ({{ device.type }}) 
                            {% if device.is_active %}
                                <span style="color: #1db954;">● Ativo</span>
                            {% endif %}
                            <br><small>Volume: {{ device.volume_percent }}%</small>
                        </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="card" style="text-align: center;">
                    <h3>🎯 Explore sua Música:</h3>
                    <a href="/search" class="btn">🔍 Buscar Músicas</a>
                    <a href="/top-tracks" class="btn">🏆 Top Músicas</a>
                    <a href="/top-artists" class="btn">🎤 Top Artistas</a>
                    <a href="/recent" class="btn">🕒 Recentes</a>
                    <a href="/stats" class="btn">📊 Estatísticas</a>
                    <a href="/logout" class="btn" style="background: #e22134;">🚪 Logout</a>
                </div>
            </div>
            
            <!-- Modal para letras -->
            <div id="lyricsModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000;">
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #282828; padding: 30px; border-radius: 15px; max-width: 600px; max-height: 80%; overflow-y: auto;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h3 id="lyricsTitle" style="color: #1db954; margin: 0;"></h3>
                        <button onclick="closeLyrics()" style="background: #e22134; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">✕</button>
                    </div>
                    <div id="lyricsContent" style="line-height: 1.6; white-space: pre-line;"></div>
                </div>
            </div>
            
            <script>
                const isPremium = {{ is_premium|lower }};
                
                async function togglePlayPause() {
                    if (!isPremium) {
                        alert('⚠️ Esta funcionalidade requer Spotify Premium');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/toggle-playback', { method: 'POST' });
                        const result = await response.json();
                        if (result.success) {
                            setTimeout(() => location.reload(), 500);
                        } else {
                            alert('Erro: ' + result.error);
                        }
                    } catch (error) {
                        alert('Erro ao controlar reprodução: ' + error);
                    }
                }
                
                async function nextTrack() {
                    if (!isPremium) {
                        alert('⚠️ Esta funcionalidade requer Spotify Premium');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/next-track', { method: 'POST' });
                        const result = await response.json();
                        if (result.success) {
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            alert('Erro: ' + result.error);
                        }
                    } catch (error) {
                        alert('Erro ao avançar música: ' + error);
                    }
                }
                
                async function previousTrack() {
                    if (!isPremium) {
                        alert('⚠️ Esta funcionalidade requer Spotify Premium');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/previous-track', { method: 'POST' });
                        const result = await response.json();
                        if (result.success) {
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            alert('Erro: ' + result.error);
                        }
                    } catch (error) {
                        alert('Erro ao voltar música: ' + error);
                    }
                }
                
                function showLyrics(trackName, artistName) {
                    document.getElementById('lyricsTitle').textContent = trackName + ' - ' + artistName;
                    document.getElementById('lyricsContent').innerHTML = `
                        <p>🎵 <strong>Onde encontrar a letra:</strong></p>
                        <p>• <a href="https://www.google.com/search?q=${encodeURIComponent(trackName + ' ' + artistName + ' letra')}" target="_blank" style="color: #1db954;">Google: "${trackName}" letra</a></p>
                        <p>• <a href="https://www.letras.mus.br/" target="_blank" style="color: #1db954;">Letras.mus.br</a></p>
                        <p>• <a href="https://genius.com/" target="_blank" style="color: #1db954;">Genius.com</a></p>
                        <p>• <a href="https://www.azlyrics.com/" target="_blank" style="color: #1db954;">AZLyrics.com</a></p>
                        <br>
                        <p><small>💡 <em>Dica: Clique nos links acima para buscar a letra em sites especializados!</em></small></p>
                    `;
                    document.getElementById('lyricsModal').style.display = 'block';
                }
                
                function shareTrack(spotifyUrl, trackName, artistName) {
                    if (navigator.share) {
                        navigator.share({
                            title: trackName + ' - ' + artistName,
                            text: 'Escute esta música no Spotify!',
                            url: spotifyUrl
                        });
                    } else {
                        // Fallback para navegadores sem Web Share API
                        const text = `🎵 Escutando: ${trackName} - ${artistName}\\n${spotifyUrl}`;
                        navigator.clipboard.writeText(text).then(() => {
                            alert('Link copiado para a área de transferência!');
                        }).catch(() => {
                            prompt('Copie este link:', spotifyUrl);
                        });
                    }
                }
                
                function closeLyrics() {
                    document.getElementById('lyricsModal').style.display = 'none';
                }
                
                // Fechar modal clicando fora
                document.getElementById('lyricsModal').onclick = function(e) {
                    if (e.target === this) {
                        closeLyrics();
                    }
                }
                
                // Auto-refresh a cada 30 segundos para atualizar música atual
                setInterval(() => {
                    if (document.visibilityState === 'visible') {
                        location.reload();
                    }
                }, 30000);
            </script>
        </body>
        </html>
        ''', 
        current_track=current_track, 
        user_name=user_profile.get('display_name', 'Usuário'),
        devices=devices,
        is_premium=is_premium
        )
        
    except Exception as e:
        return f"Erro ao carregar dashboard: {e}"

# Adicionar nova rota para estatísticas
@app.route('/stats')
def stats():
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    
    try:
        # Top tracks e artistas em diferentes períodos
        top_tracks_short = sp.current_user_top_tracks(limit=5, time_range='short_term')
        top_tracks_medium = sp.current_user_top_tracks(limit=5, time_range='medium_term')
        top_artists_short = sp.current_user_top_artists(limit=5, time_range='short_term')
        top_artists_medium = sp.current_user_top_artists(limit=5, time_range='medium_term')
        
        # Processar dados dos artistas para evitar erros de template
        def process_artists(artists_data):
            processed = []
            for artist in artists_data['items']:
                genres_text = "Gênero não especificado"
                if artist.get('genres') and len(artist['genres']) > 0:
                    genres_list = artist['genres'][:3]  # Pegar até 3 gêneros
                    genres_text = ', '.join(genres_list)
                
                processed.append({
                    'name': artist['name'],
                    'popularity': artist.get('popularity', 0),
                    'genres_text': genres_text,
                    'followers': artist.get('followers', {}).get('total', 0)
                })
            return processed
        
        artists_short_processed = process_artists(top_artists_short)
        artists_medium_processed = process_artists(top_artists_medium)
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Estatísticas - Spotify App</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #191414; color: white; }
                .container { max-width: 1000px; margin: 0 auto; }
                .btn { background: #1db954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }
                .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
                .stat-card { background: #282828; padding: 20px; border-radius: 10px; }
                h1, h2 { color: #1db954; }
                ul { list-style: none; padding: 0; }
                li { background: #333; margin: 8px 0; padding: 12px; border-radius: 5px; }
                .period { background: #1db954; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; margin-bottom: 15px; display: inline-block; }
                .track-info, .artist-info { color: #b3b3b3; font-size: 0.9em; margin-top: 5px; }
                .rank { color: #1db954; font-weight: bold; margin-right: 8px; }
                @media (max-width: 768px) { .stats-grid { grid-template-columns: 1fr; } }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Suas Estatísticas Musicais</h1>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <span class="period">🔥 ÚLTIMAS 4 SEMANAS</span>
                        <h2>🎵 Top 5 Músicas</h2>
                        <ul>
                        {% for track in top_tracks_short.items %}
                            <li>
                                <span class="rank">{{ loop.index }}.</span>
                                <strong>{{ track.name }}</strong><br>
                                <div class="track-info">🎤 {{ track.artists[0].name }}</div>
                                <div class="track-info">⭐ {{ track.popularity }}/100</div>
                            </li>
                        {% endfor %}
                        </ul>
                    </div>
                    
                    <div class="stat-card">
                        <span class="period">📅 ÚLTIMOS 6 MESES</span>
                        <h2>🎵 Top 5 Músicas</h2>
                        <ul>
                        {% for track in top_tracks_medium.items %}
                            <li>
                                <span class="rank">{{ loop.index }}.</span>
                                <strong>{{ track.name }}</strong><br>
                                <div class="track-info">🎤 {{ track.artists[0].name }}</div>
                                <div class="track-info">⭐ {{ track.popularity }}/100</div>
                            </li>
                        {% endfor %}
                        </ul>
                    </div>
                    
                    <div class="stat-card">
                        <span class="period">🔥 ÚLTIMAS 4 SEMANAS</span>
                        <h2>🎤 Top 5 Artistas</h2>
                        <ul>
                        {% for artist in artists_short_processed %}
                            <li>
                                <span class="rank">{{ loop.index }}.</span>
                                <strong>{{ artist.name }}</strong><br>
                                <div class="artist-info">🎵 {{ artist.genres_text }}</div>
                                <div class="artist-info">⭐ {{ artist.popularity }}/100</div>
                            </li>
                        {% endfor %}
                        </ul>
                    </div>
                    
                    <div class="stat-card">
                        <span class="period">📅 ÚLTIMOS 6 MESES</span>
                        <h2>🎤 Top 5 Artistas</h2>
                        <ul>
                        {% for artist in artists_medium_processed %}
                            <li>
                                <span class="rank">{{ loop.index }}.</span>
                                <strong>{{ artist.name }}</strong><br>
                                <div class="artist-info">🎵 {{ artist.genres_text }}</div>
                                <div class="artist-info">⭐ {{ artist.popularity }}/100</div>
                            </li>
                        {% endfor %}
                        </ul>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/dashboard" class="btn">← Voltar ao Dashboard</a>
                    <a href="/top-tracks" class="btn">🏆 Ver Mais Músicas</a>
                    <a href="/top-artists" class="btn">🎤 Ver Mais Artistas</a>
                </div>
            </div>
        </body>
        </html>
        ''', 
        top_tracks_short=top_tracks_short,
        top_tracks_medium=top_tracks_medium,
        artists_short_processed=artists_short_processed,
        artists_medium_processed=artists_medium_processed
        )
        
    except Exception as e:
        return f"Erro ao carregar estatísticas: {e}"

@app.route('/top-artists')
def top_artists():
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    
    try:
        top_artists_data = sp.current_user_top_artists(limit=20, time_range='medium_term')
        
        # Processar dados para evitar erros
        processed_artists = []
        for artist in top_artists_data['items']:
            genres_text = "Gênero não especificado"
            if artist.get('genres') and len(artist['genres']) > 0:
                genres_list = artist['genres'][:3]  # Pegar até 3 gêneros
                genres_text = ', '.join(genres_list)
            
            followers_count = artist.get('followers', {}).get('total', 0)
            followers_formatted = "{:,}".format(followers_count).replace(',', '.')
            
            processed_artists.append({
                'name': artist['name'],
                'popularity': artist.get('popularity', 0),
                'genres_text': genres_text,
                'followers_formatted': followers_formatted
            })
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Top Artistas - Spotify App</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #191414; color: white; }
                .container { max-width: 800px; margin: 0 auto; }
                .btn { background: #1db954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }
                ul { list-style: none; padding: 0; }
                li { background: #282828; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .rank { background: #1db954; color: white; padding: 5px 10px; border-radius: 50%; margin-right: 10px; font-size: 14px; }
                h1 { color: #1db954; }
                .genres { color: #b3b3b3; font-size: 0.9em; margin-top: 5px; }
                .popularity { color: #ffd700; margin-left: 10px; }
                .followers { color: #b3b3b3; font-size: 0.9em; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎤 Seus Top 20 Artistas</h1>
                <p style="color: #b3b3b3; text-align: center; margin-bottom: 30px;">Baseado nos últimos 6 meses</p>
                
                <ul>
                {% for artist in processed_artists %}
                    <li>
                        <span class="rank">{{ loop.index }}</span>
                        <strong>{{ artist.name }}</strong>
                        <span class="popularity">⭐ {{ artist.popularity }}/100</span><br>
                        <div class="genres">🎵 {{ artist.genres_text }}</div>
                        <div class="followers">👥 {{ artist.followers_formatted }} seguidores</div>
                    </li>
                {% endfor %}
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/dashboard" class="btn">← Voltar ao Dashboard</a>
                    <a href="/stats" class="btn">📊 Ver Estatísticas</a>
                </div>
            </div>
        </body>
        </html>
        ''', processed_artists=processed_artists)
        
    except Exception as e:
        return f"Erro ao carregar top artistas: {e}"
    
# APIs para controle de reprodução (com verificação Premium)
@app.route('/api/toggle-playback', methods=['POST'])
def toggle_playback():
    sp = get_spotify_client()
    if not sp:
        return jsonify({'success': False, 'error': 'Não autenticado'})
    
    if not check_premium(sp):
        return jsonify({'success': False, 'error': 'Spotify Premium necessário'})
    
    try:
        current = sp.current_user_playing_track()
        if current and current['is_playing']:
            sp.pause_playback()
        else:
            sp.start_playback()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/next-track', methods=['POST'])
def next_track():
    sp = get_spotify_client()
    if not sp:
        return jsonify({'success': False, 'error': 'Não autenticado'})
    
    if not check_premium(sp):
        return jsonify({'success': False, 'error': 'Spotify Premium necessário'})
    
    try:
        sp.next_track()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/previous-track', methods=['POST'])
def previous_track():
    sp = get_spotify_client()
    if not sp:
        return jsonify({'success': False, 'error': 'Não autenticado'})
    
    if not check_premium(sp):
        return jsonify({'success': False, 'error': 'Spotify Premium necessário'})
    
    try:
        sp.previous_track()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Manter outras rotas existentes...
@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = None
    tracks = []
    
    if query:
        sp = get_spotify_client()
        if sp:
            try:
                results = sp.search(q=query, type='track', limit=15)
                if results and 'tracks' in results and 'items' in results['tracks']:
                    tracks = results['tracks']['items']
            except Exception as e:
                return f"Erro na busca: {e}"
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Buscar - Spotify App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #191414; color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            input { padding: 12px; width: 350px; border: none; border-radius: 25px; margin-right: 10px; font-size: 16px; }
            button { background: #1db954; color: white; padding: 12px 25px; border: none; border-radius: 25px; cursor: pointer; font-size: 16px; }
            .btn { background: #1db954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            ul { list-style: none; padding: 0; }
            li { background: #282828; margin: 15px 0; padding: 20px; border-radius: 10px; }
            h1 { color: #1db954; }
            .track-name { font-size: 1.2em; font-weight: bold; margin-bottom: 8px; }
            .track-info { color: #b3b3b3; margin: 5px 0; }
            .spotify-btn { background: #1db954; color: white; padding: 8px 15px; text-decoration: none; border-radius: 20px; font-size: 14px; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Buscar Músicas</h1>
            
            <form method="GET" style="text-align: center; margin: 30px 0;">
                <input type="text" name="q" value="{{ query }}" placeholder="Digite o nome da música, artista ou álbum..." autofocus>
                <button type="submit">🔍 Buscar</button>
            </form>
            
            {% if tracks %}
                <h2>Resultados ({{ tracks|length }}):</h2>
                <ul>
                {% for track in tracks %}
                    <li>
                        <div class="track-name">{{ track.name }}</div>
                        <div class="track-info">🎤 {{ track.artists[0].name }}</div>
                        <div class="track-info">💿 {{ track.album.name }} ({{ track.album.release_date[:4] }})</div>
                        <div class="track-info">⭐ {{ track.popularity }}/100 | ⏱️ {{ (track.duration_ms // 60000) }}:{{ '%02d'|format((track.duration_ms % 60000) // 1000) }}</div>
                        <div style="margin-top: 10px;">
                            <a href="{{ track.external_urls.spotify }}" target="_blank" class="spotify-btn">🎧 Abrir no Spotify</a>
                            <button class="spotify-btn" onclick="showLyrics('{{ track.name }}', '{{ track.artists[0].name }}')" style="background: #e22134; border: none; cursor: pointer;">📝 Letra</button>
                        </div>
                    </li>
                {% endfor %}
                </ul>
            {% elif query %}
                <div style="text-align: center; margin: 40px 0;">
                    <h3>😔 Nenhum resultado encontrado</h3>
                    <p>Tente buscar por outro termo: "{{ query }}"</p>
                </div>
            {% else %}
                <div style="text-align: center; margin: 40px 0; color: #b3b3b3;">
                    <p>💡 Digite algo para buscar músicas, artistas ou álbuns...</p>
                    <p><small>Exemplos: "Anitta", "rock nacional", "samba"</small></p>
                </div>
            {% endif %}
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/dashboard" class="btn">← Voltar ao Dashboard</a>
            </div>
        </div>
        
        <script>
            function showLyrics(trackName, artistName) {
                const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(trackName + ' ' + artistName + ' letra')}`;
                window.open(searchUrl, '_blank');
            }
        </script>
    </body>
    </html>
    ''', query=query, tracks=tracks)

# Manter outras rotas (recent, top-tracks, logout)...
@app.route('/recent')
def recent_tracks():
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    
    try:
        recent = sp.current_user_recently_played(limit=30)
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Músicas Recentes - Spotify App</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #191414; color: white; }
                .container { max-width: 800px; margin: 0 auto; }
                .btn { background: #1db954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                ul { list-style: none; padding: 0; }
                li { background: #282828; margin: 10px 0; padding: 15px; border-radius: 5px; }
                h1 { color: #1db954; }
                .time { color: #b3b3b3; font-size: 0.9em; }
                .spotify-link { background: #1db954; color: white; padding: 5px 10px; text-decoration: none; border-radius: 15px; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🕒 Músicas Tocadas Recentemente</h1>
                
                <ul>
                {% for item in recent.items %}
                    <li>
                        <strong>{{ item.track.name }}</strong><br>
                        <em>{{ item.track.artists[0].name }}</em><br>
                        <div class="time">📅 {{ item.played_at[:10] }} às {{ item.played_at[11:16] }}</div>
                        <div style="margin-top: 8px;">
                            <a href="{{ item.track.external_urls.spotify }}" target="_blank" class="spotify-link">🎧 Abrir no Spotify</a>
                        </div>
                    </li>
                {% endfor %}
                </ul>
                
                <a href="/dashboard" class="btn">← Voltar ao Dashboard</a>
            </div>
        </body>
        </html>
        ''', recent=recent)
        
    except Exception as e:
        return f"Erro ao carregar músicas recentes: {e}"

@app.route('/top-tracks')
def top_tracks():
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    
    try:
        top_tracks = sp.current_user_top_tracks(limit=25, time_range='medium_term')
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Top Músicas - Spotify App</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #191414; color: white; }
                .container { max-width: 800px; margin: 0 auto; }
                .btn { background: #1db954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                ul { list-style: none; padding: 0; }
                li { background: #282828; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .rank { background: #1db954; color: white; padding: 8px 12px; border-radius: 50%; margin-right: 15px; font-weight: bold; }
                h1 { color: #1db954; }
                .spotify-link { background: #1db954; color: white; padding: 5px 10px; text-decoration: none; border-radius: 15px; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏆 Suas Top 25 Músicas</h1>
                <p style="color: #b3b3b3; text-align: center;">Baseado nos últimos 6 meses</p>
                
                <ul>
                {% for track in top_tracks.items %}
                    <li>
                        <span class="rank">{{ loop.index }}</span>
                        <strong>{{ track.name }}</strong><br>
                        <em>{{ track.artists[0].name }}</em><br>
                        <small>Popularidade: {{ track.popularity }}/100</small>
                        <div style="margin-top: 8px;">
                            <a href="{{ track.external_urls.spotify }}" target="_blank" class="spotify-link">🎧 Abrir no Spotify</a>
                        </div>
                    </li>
                {% endfor %}
                </ul>
                
                <a href="/dashboard" class="btn">← Voltar ao Dashboard</a>
            </div>
        </body>
        </html>
        ''', top_tracks=top_tracks)
        
    except Exception as e:
        return f"Erro ao carregar top tracks: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)