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

app = Flask(__name__, template_folder='templates')
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'downloads')
MAX_WORKERS = 4

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
    return """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
          <title>🎵 Téléchargeur YouTube MP3</title>
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
          <style>
            :root {
              --bg-gradient: linear-gradient(135deg, #2e026d, #1e1b4b, #312e81);
              --glass-bg: rgba(255, 255, 255, 0.05);
              --border: rgba(255, 255, 255, 0.3);
              --text-white: #fff;
              --text-muted: #b0b8d0;
              --blue: #60a5fa;
              --red: #f87171;
              --green: #4ade80;
              --purple: #a78bfa;
              --transition: all 0.3s ease;
            }

            body {
              margin: 0;
              font-family: 'Inter', sans-serif;
              background: var(--bg-gradient);
              color: var(--text-white);
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              padding: 1rem;
            }

            .container {
              max-width: 700px;
              width: 100%;
              background: var(--glass-bg);
              backdrop-filter: blur(16px);
              border: 1px solid var(--border);
              border-radius: 1.5rem;
              padding: 2rem;
              box-shadow: 0 12px 32px rgba(0,0,0,0.2);
              animation: fadeInUp 0.5s ease;
            }

            h2 {
              text-align: center;
              font-size: 2rem;
              margin-bottom: 1rem;
              font-weight: 800;
              color: var(--text-white);
            }

            .subtitle {
              text-align: center;
              color: var(--text-muted);
              margin-bottom: 2rem;
            }

            label {
              font-weight: 600;
              margin-top: 1rem;
              display: block;
              color: var(--text-white);
            }

            textarea, input {
              width: 100%;
              padding: 12px;
              margin-top: 0.5rem;
              border: 1px solid var(--border);
              border-radius: 0.75rem;
              background: rgba(255,255,255,0.1);
              color: var(--text-white);
              font-size: 1rem;
              outline: none;
              transition: var(--transition);
            }

            textarea::placeholder,
            input::placeholder {
              color: rgba(255,255,255,0.6);
            }

            textarea:focus, input:focus {
              border-color: var(--purple);
              box-shadow: 0 0 0 3px rgba(167,139,250,0.3);
            }

            button {
              margin-top: 1.5rem;
              width: 100%;
              background-color: var(--purple);
              color: var(--text-white);
              font-weight: 600;
              padding: 12px;
              border: none;
              border-radius: 0.75rem;
              cursor: pointer;
              font-size: 1rem;
              transition: var(--transition);
            }

            button:hover {
              filter: brightness(1.1);
            }

            .progress-bar {
              width: 100%;
              background-color: rgba(255,255,255,0.1);
              border-radius: 6px;
              margin: 1.5rem 0;
              height: 10px;
              overflow: hidden;
              display: none;
            }

            .progress {
              height: 100%;
              width: 0%;
              background-color: var(--purple);
              transition: width 0.4s ease-in-out;
            }

            .status {
              text-align: center;
              font-size: 1rem;
              margin-top: 1rem;
            }

            .status.success { color: var(--green); }
            .status.error { color: var(--red); }

            pre {
              background: rgba(255,255,255,0.1);
              padding: 1rem;
              border-radius: 0.75rem;
              overflow-x: auto;
              color: var(--text-white);
              margin-top: 1rem;
            }

            @keyframes fadeInUp {
              from { opacity: 0; transform: translateY(15px);}
              to { opacity: 1; transform: translateY(0);}
            }

            /* Responsive */
            @media(max-width:768px){
              .container { padding: 1.5rem; }
              h2 { font-size: 1.6rem; }
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h2>🎵 Téléchargeur MP3 YouTube</h2>
            <p class="subtitle">Télécharge tes musiques préférées rapidement et facilement</p>

            <form id="downloadForm">
              <label for="urls">Liste des URLs YouTube :</label>
              <textarea id="urls" name="urls" rows="5" placeholder="https://www.youtube.com/watch?v=..."></textarea>

              <label for="quality">Qualité audio :</label>
              <input type="text" id="quality" name="quality" value="192" placeholder="192 (par défaut)">

              <button type="submit">📥 Télécharger</button>
            </form>

            <div class="progress-bar" id="progressBar">
              <div class="progress" id="progressFill"></div>
            </div>

            <div class="status" id="statusText"></div>
            <div id="result"></div>
          </div>

          <script>
            const form = document.getElementById('downloadForm');
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            const statusText = document.getElementById('statusText');
            const resultDiv = document.getElementById('result');

            function resetProgress() {
              progressFill.style.width = '0%';
              progressBar.style.display = 'block';
            }

            function updateProgress(percent) {
              progressFill.style.width = percent + '%';
            }

            function showStatus(message, type='') {
              statusText.innerHTML = message;
              statusText.className = `status ${type}`;
            }

            form.addEventListener('submit', async (e) => {
              e.preventDefault();
              const urls = document.getElementById('urls').value.trim().split('\n').filter(u=>u);
              const quality = document.getElementById('quality').value || '192';

              if(!urls.length){ showStatus("Veuillez entrer au moins une URL.", 'error'); return; }

              resetProgress();
              updateProgress(10);
              showStatus("⏳ Téléchargement en cours...");

              try{
                const response = await fetch('/api/download',{
                  method: 'POST',
                  headers: {'Content-Type':'application/json'},
                  body: JSON.stringify({urls, quality, parallel:true})
                });

                updateProgress(70);
                const data = await response.json();
                updateProgress(100);

                if(data.success){
                  showStatus("✅ Téléchargement terminé !", 'success');
                  resultDiv.innerHTML = `<pre>
        Session ID : ${data.session_id}
        Téléchargements réussis : ${data.stats.success} / ${data.stats.total}
        Échecs : ${data.stats.failed}
                  </pre>`;
                } else {
                  showStatus(`❌ ${data.message}`, 'error');
                }
              } catch(err){
                showStatus("❌ Erreur côté client : " + err.message,'error');
              }

              setTimeout(()=>{ progressBar.style.display='none'; updateProgress(0); }, 2000);
            });
          </script>
        </body>
        </html>
    """

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
