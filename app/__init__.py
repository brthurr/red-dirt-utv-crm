import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access the shop.'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.customers import customers_bp
    from app.routes.machines import machines_bp
    from app.routes.repair_orders import ro_bp
    from app.routes.inventory import inventory_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(machines_bp)
    app.register_blueprint(ro_bp)
    app.register_blueprint(inventory_bp)

    return app
