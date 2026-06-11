from flask import Flask
from config import Config
from database.db import init_db
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.hr_routes import hr_bp
from routes.manager_routes import manager_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    with app.app_context():
        init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(manager_bp, url_prefix='/manager')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
