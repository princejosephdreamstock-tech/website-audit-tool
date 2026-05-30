#!/usr/bin/env python3
"""
Website Audit Tool — Standalone Backend
"""
import requests as req, re, time as t
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({'service': 'Website Audit API', 'usage': 'POST /audit with {"url":"https://site.com"}'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/audit', methods=['POST'])
def audit():
    data = request.get_json()
    url = data.get('url', '')
    if not url: return jsonify({'success': False, 'error': 'No URL'})
    if not url.startswith('http'): url = 'https://' + url
    
    start = t.time()
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}
        r = req.get(url, headers=headers, timeout=15)
        load_time = round(t.time() - start, 2)
        html = r.text.lower()
        size_kb = round(len(r.content) / 1024, 1)
        
        has_https = url.startswith('https')
        has_title = bool(re.search(r'<title>[^<]+</title>', html))
        has_desc = bool(re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html))
        has_viewport = 'viewport' in html and 'width=device-width' in html
        has_h1 = '<h1' in html
        has_alt = len(re.findall(r'<img[^>]*alt="[^"]*"', html))
        total_img = max(len(re.findall(r'<img[^>]*>', html)), 1)
        
        overall = int(sum([
            100 if has_https else 0, 100 if load_time < 3 else 70 if load_time < 5 else 30,
            100 if has_viewport else 0, 100 if has_title else 0, 100 if has_desc else 0,
            100 if has_h1 else 0, round((has_alt / total_img) * 100),
            100 if size_kb < 500 else 70 if size_kb < 1000 else 40, 100 if r.status_code == 200 else 0
        ]) / 9)
        
        return jsonify({'success': True, 'load_time': load_time, 'size_kb': size_kb,
                       'status': r.status_code, 'ssl': has_https, 'title': has_title,
                       'description': has_desc, 'mobile': has_viewport, 'h1': has_h1,
                       'alt_tags': round((has_alt / total_img) * 100), 'overall': overall})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:100]})

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
