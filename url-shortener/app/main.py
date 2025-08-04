from flask import Flask, jsonify, request, redirect
from datetime import datetime
import threading
from .models import URLStore
from .utils import generate_short_code, is_valid_url

app = Flask(__name__)

url_store=URLStore()
lock=threading.Lock()

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "URL Shortener API"
    })

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "message": "URL Shortener API is running"
    })
    
@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "URL Is Not Found"}), 400
        url=data['url'].strip()
        if not is_valid_url(url):
            return jsonify({"error": "Invalid URL Formate"}), 400

        with lock:
                short_code = generate_short_code()
                while url_store.get_url(short_code) is not None:
                    short_code = generate_short_code()
                url_store.store_url(short_code, url)
        return jsonify({
            "short_code": short_code,
            "short_url": f'http://localhost:5000/{short_code}',
        })
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500  

@app.route('/<short_code>')
def redirect_url(short_code):
    if len(short_code) != 6 or not short_code.isalnum():
        return jsonify({'error': 'Invalid short code format'}), 404
    
    with lock:
        url_data=url_store.get_url(short_code)
        if url_data is None:
            return jsonify({'error': 'Short code not found'}), 404
        url_store.increment_clicks(short_code)
        original_url = url_data['url']
    return redirect(original_url, code=302)
    
@app.route('/api/stats/<short_code>')
def get_stats(short_code):
    if len(short_code) != 6 or not short_code.isalnum():
        return jsonify({'error': 'Invalid short code format'}), 404
    
    with lock:
        url_data = url_store.get_url(short_code)
    
    if url_data is None:
        return jsonify({'error': 'Short code not found'}), 404
    
    return jsonify({
        'url': url_data['url'],
        'clicks': url_data['clicks'],
        'created_at': url_data['created_at']
    })
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)