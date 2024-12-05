from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
from youtubesearchpython import VideosSearch
import requests
import httpx
from flask_cors import CORS


app = Flask(__name__)

CORS(app)

app.secret_key = 'sua_chave_secreta'  # Necessária para usar sessões


# Configuração do proxy
PROXY = {
    "http": "http://joailson:Axl130213a@proxy.educacao.parana:8080",
    "https": "http://joailson:Axl130213a@proxy.educacao.parana:8080"
}

DOWNLOAD_FOLDER = 'downloads'


# Função para obter o link de download
def get_video_download_link(url):
    try:
        ap = 25
        yt = YouTube(url, on_progress_callback=on_progress)
        streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        if streams:
            best_stream = streams.first()
            return best_stream.url, yt.title
        else:
            return None
    except Exception as e:
        return None

def download_video(url):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        filename = stream.download(output_path=DOWNLOAD_FOLDER)
        return filename
    except Exception as e:
        print(f"Erro ao baixar vídeo: {e}")
        return None



# Configurando proxy global
#os.environ['HTTP_PROXY'] = PROXY['http']
#os.environ['HTTPS_PROXY'] = PROXY['https']

def search_videos(query, max_results=15):
    """Função para pesquisar vídeos usando requests diretamente"""
    api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults={max_results}&key=AIzaSyDeFpROQLpC4yFo1VLJoN3VLz3lbKoQQk0"

    try:
        #response = requests.get(api_url, proxies=PROXY)
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

    videos = search_videos(query)  # Função que realiza a busca
    return jsonify(videos)


# Rota para receber a URL do vídeo
@app.route('/submit', methods=['POST'])
def submit_video():
    data = request.form
    video_url = data.get('url')
    url = data.get('url')

    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400
    # Salva a URL na sessão para reutilização posterior
    session['original_video_url'] = video_url
    download_link, title = get_video_download_link(video_url)
    stream_url = download_link
    

    if download_link:
        #return redirect(url_for('download_page', video_url=download_link, url=url))
        return jsonify({"stream_url": download_link, "title": title}) 
    else:
        return jsonify({'error': 'Failed to get the video'}), 500
 
# Rota dinâmica para exibir o botão de download
@app.route('/<path:video_url>')
def download_page(video_url,):

    return render_template('download_page.html', download_link=video_url)

@app.route('/download_video', methods=['POST'])
def serve_download():
    #video_url = request.form.get('url')
    #video_url = 'https://www.youtube.com/watch?v=HlEuo9aR7Qo'
    # Recupera a URL original da sessão
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
