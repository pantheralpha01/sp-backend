import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from models import db
from routes import api
from auth_routes import auth_bp
from shift_routes import shifts_bp
from transaction_routes import transactions_bp
from expense_routes import expenses_bp
from report_routes import reports_bp

def create_app(env='development'):
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[env])

    # Initialize extensions
    db.init_app(app)
    JWTManager(app)

    # Enable CORS — allow Authorization header for JWT
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })

    # Register blueprints
    app.register_blueprint(api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(shifts_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(reports_bp)

    # Serve admin dashboard
    @app.route('/', methods=['GET'])
    def admin_dashboard():
        """Serve admin dashboard"""
        admin_file = os.path.join(os.path.dirname(__file__), 'admin.html')
        with open(admin_file, 'r', encoding='utf-8') as f:
            return f.read()

    # Create all tables
    with app.app_context():
        db.create_all()

    return app

# Create app instance for Gunicorn/production
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    print("\n" + "="*50)
    print("SP Backend Server Starting...")
    print("="*50)
    print("\nAdmin Dashboard: http://localhost:5000")
    print("API Base: http://localhost:5000/api")
    print("\nAuth:")
    print("  GET  /api/auth/setup/status")
    print("  POST /api/auth/setup")
    print("  POST /api/auth/login")
    print("  GET  /api/auth/me")
    print("  GET  /api/auth/users")
    print("  POST /api/auth/users")
    print("\nProducts:")
    print("  GET  /api/products")
    print("  POST /api/products/upload")
    print("  GET  /api/categories")
    print("  GET  /api/stats")
    print("\nShifts:")
    print("  POST /api/shifts")
    print("  GET  /api/shifts/current")
    print("  PUT  /api/shifts/<id>/close")
    print("  GET  /api/shifts/<id>/summary")
    print("\nTransactions:")
    print("  POST /api/transactions")
    print("  POST /api/transactions/batch")
    print("  GET  /api/transactions")
    print("\nExpenses:")
    print("  POST /api/expenses")
    print("  GET  /api/expenses")
    print("  PUT  /api/expenses/<id>/approve")
    print("  PUT  /api/expenses/<id>/reject")
    print("\nReports:")
    print("  GET  /api/reports/daily")
    print("  GET  /api/reports/range")
    print("  GET  /api/reports/cashier/<id>")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=True
    )
