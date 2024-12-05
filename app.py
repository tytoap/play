from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
from flask_cors import CORS
import requests

app = Flask(__name__)

CORS(app)

app.secret_key = 'sua_chave_secreta'  # Necessária para usar sessões

DOWNLOAD_FOLDER = 'downloads'

# Função para obter o link de download
def get_video_download_link(url):
    try:
        visitor_data = 'CgtUdWJWZ0xoNEdyWSiA68a6BjIKCgJCUhIEGgAgHw%3D%3D'
        po_token = 'MnRCjSW2EGRxM0K16T90u8fk3tKGno-iEYDcOe-c6jcGrEE7nvXljT0pCP9BCE_ueXkXY-JeEfwn2l3_J6W4wjo-NX_KkPCLo0kk-hZTA9_6fIUe3p1OHBTP7DyZXkCt0Mf0GIIufirsiKSSvWvYP7HmiBgJaQ=='

        yt = YouTube(url, on_progress_callback=on_progress, use_po_token=True)
        streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        if streams:
            best_stream = streams.first()
            return best_stream.url, yt.title
        else:
            return None, None
    except Exception as e:
        print(f"Erro ao obter o link: {e}")
        return None, None

def download_video(url):
    visitor_data = 'CgtUdWJWZ0xoNEdyWSiA68a6BjIKCgJCUhIEGgAgHw%3D%3D'
    po_token = 'MnRCjSW2EGRxM0K16T90u8fk3tKGno-iEYDcOe-c6jcGrEE7nvXljT0pCP9BCE_ueXkXY-JeEfwn2l3_J6W4wjo-NX_KkPCLo0kk-hZTA9_6fIUe3p1OHBTP7DyZXkCt0Mf0GIIufirsiKSSvWvYP7HmiBgJaQ=='

    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        filename = stream.download(output_path=DOWNLOAD_FOLDER)
        return filename
    except Exception as e:
        print(f"Erro ao baixar vídeo: {e}")
        return None

def search_videos(query, max_results=15):
    """Função para pesquisar vídeos usando a API do YouTube"""
    api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults={max_results}&key=AIzaSyDeFpROQLpC4yFo1VLJoN3VLz3lbKoQQk0"

    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Levanta um erro se a resposta HTTP não for 200
        results = response.json().get('items', [])
        
        return [
            {
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
            }
            for item in results
        ]
    except Exception as e:
        print(f"Erro ao buscar vídeos: {e}")
        return []

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return jsonify({"error": "Nenhuma consulta fornecida"}), 400

    videos = search_videos(query)
    return jsonify(videos)

# Rota para receber a URL do vídeo
@app.route('/submit', methods=['POST'])
def submit_video():
    data = request.form
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    session['original_video_url'] = video_url
    download_link, title = get_video_download_link(video_url)

    if download_link:
        return jsonify({"stream_url": download_link, "title": title})
    else:
        return jsonify({'error': 'Failed to get the video'}), 500

@app.route('/download_video', methods=['POST'])
def serve_download():
    video_url = session.get('original_video_url')
    file_path = download_video(video_url)
    
    if file_path:
        return send_file(file_path, as_attachment=True)
    else:
        return "Erro ao processar o download", 500

@app.route('/')
def index():
    return render_template('search.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
