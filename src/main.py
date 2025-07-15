import os
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from routes.chatbot import chatbot_bp

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)  # Enable CORS for all routes

app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    # The port is now handled by Gunicorn via Procfile in production
    # For local development, Flask's default 5000 is fine, or you can specify
    # However, for consistency with HF Spaces, we'll ensure it can run on 7860
    port = int(os.environ.get('PORT', 7860))  # Use 7860 as default for local testing too
    app.run(host='0.0.0.0', port=port, debug=True)
