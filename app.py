from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Disable output buffering
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.contacts import contacts_bp
from api.analytics import analytics_bp
from api.email import email_bp
from api.filters import filters_bp
from api.lead_discovery import lead_discovery_bp
from api.campaigns import campaigns_bp
from api.email_templates import templates_bp
from config import DEBUG, HOST, PORT

app = Flask(__name__)
CORS(app)

# Register all blueprints
app.register_blueprint(contacts_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(email_bp, url_prefix='/api')
app.register_blueprint(filters_bp, url_prefix='/api')
app.register_blueprint(lead_discovery_bp, url_prefix='/api')
app.register_blueprint(campaigns_bp, url_prefix='/api')
app.register_blueprint(templates_bp, url_prefix='/api')

@app.route('/')
def index():
    return jsonify({
        'message': 'Everly Studio Lead Generation Engine API',
        'version': '2.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/email/test', methods=['GET'])
def test_email_connection():
    """Test email SMTP connection"""
    from services.email_service import EmailService
    email_service = EmailService()
    result = email_service.test_connection()
    return jsonify(result)

if __name__ == '__main__':
    print("=" * 60, flush=True)
    print("🚀 Everly Studio Lead Generation Engine", flush=True)
    print("=" * 60, flush=True)
    print(f"Server running on: http://{HOST}:{PORT}", flush=True)
    print("Press CTRL+C to stop", flush=True)
    print("=" * 60, flush=True)
    app.run(host=HOST, port=PORT, debug=DEBUG)