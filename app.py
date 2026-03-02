import os
from flask import Flask, render_template_string, send_file
from flask_cors import CORS
from config import config
from models import db
from routes import api

def create_app(env='development'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[env])
    
    # Initialize database
    db.init_app(app)
    
    # Enable CORS (allow requests from Flutter app)
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Serve admin dashboard
    @app.route('/', methods=['GET'])
    def admin_dashboard():
        """Serve admin dashboard"""
        admin_file = os.path.join(os.path.dirname(__file__), 'admin.html')
        with open(admin_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    print("\n" + "="*50)
    print("🚀 SP Backend Server Starting...")
    print("="*50)
    print("\n📊 Admin Dashboard: http://localhost:5000")
    print("📡 API Base: http://localhost:5000/api")
    print("\nAvailable endpoints:")
    print("  GET  /api/products")
    print("  POST /api/products/upload")
    print("  GET  /api/categories")
    print("  GET  /api/stats")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=True
    )
