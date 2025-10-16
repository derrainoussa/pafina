from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
from pathlib import Path
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor
import tempfile
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'downloads')
MAX_WORKERS = 3

def telecharger_audio(youtube_url, dossier_de_sortie, qualite='192'):
    try:
        Path(dossier_de_sortie).mkdir(parents=True, exist_ok=True)
        
        options = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(dossier_de_sortie, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': qualite,
            }],
            'quiet': True,
            'no_warnings': True,
            'nooverwrites': True,
            'restrictfilenames': True,
        }
        
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            titre = info.get('title', 'Sans titre')
            is_playlist = 'entries' in info
            
            ydl.download([youtube_url])
            
            return {
                'success': True,
                'url': youtube_url,
                'title': titre,
                'is_playlist': is_playlist,
                'message': 'Téléchargement réussi'
            }
    except Exception as e:
        return {
            'success': False,
            'url': youtube_url,
            'message': f'Erreur: {str(e)}'
        }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        quality = data.get('quality', '192')
        parallel = data.get('parallel', True)
        max_workers = min(int(data.get('max_workers', 3)), 5)
        
        if not urls:
            return jsonify({'success': False, 'message': 'Aucune URL fournie'}), 400
        
        urls = list(dict.fromkeys([url.strip() for url in urls if url.strip()]))
        
        session_id = str(uuid.uuid4())
        dossier_sortie = os.path.join(UPLOAD_FOLDER, f'youtube_dl_{session_id}')
        
        resultats = []
        
        if parallel and len(urls) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(telecharger_audio, url, dossier_sortie, quality): url for url in urls}
                for future in futures:
                    resultats.append(future.result())
        else:
            for url in urls:
                resultats.append(telecharger_audio(url, dossier_sortie, quality))
        
        success_count = sum(1 for r in resultats if r['success'])
        
        return jsonify({
            'success': True,
            'results': resultats,
            'stats': {
                'total': len(resultats),
                'success': success_count,
                'failed': len(resultats) - success_count
            },
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/info', methods=['POST'])
def get_info():
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'success': False, 'message': 'URL manquante'}), 400
        
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'Sans titre'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Inconnu'),
                'is_playlist': 'entries' in info
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Railway attribue le port automatiquement
    app.run(host='0.0.0.0', port=port)
