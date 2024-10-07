import os
import logging
from flask import Flask
from flask_migrate import Migrate
from app.models import db
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_cors import CORS
from .assets import compile_static_assets
from .parse_json import consolidate_json_files
from datetime import datetime, timezone
from datetime import timedelta

UTC = timezone.utc

migrate = Migrate()
mail = Mail()

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Get allowed origins from BASE_URL and split to allow multiple origins
base_url = os.getenv('BASE_URL', 'http://127.0.0.1:8000')
allowed_origins = base_url.split(',')

# Check if Redis should be used
use_redis = os.getenv('USE_REDIS', 'False').lower() in ['true', '1', 't']
redis_url = os.getenv(
    'REDIS_URL', 'redis://127.0.0.1:6379/0') if use_redis else None
use_flask = os.getenv('USE_FLASK', 'False').lower() in [
    'true', '1', 't']  # Use Flask Server for local development

# Log whether Redis is being used
if use_redis:
    logging.info(f"Using Redis as a message queue: {redis_url}")
    socketio_config = {
        'manage_session': True,
        'cors_allowed_origins': allowed_origins,
        'message_queue': redis_url
    }
else:
    logging.info("Not using Redis; falling back to local sessions.")
    socketio_config = {
        'manage_session': True,
        'cors_allowed_origins': allowed_origins
    }

# Set async_mode if not using Flask
if not use_flask:
    socketio_config['async_mode'] = 'eventlet'

socketio = SocketIO(**socketio_config)


def create_app():
    app = Flask(__name__)

    # Ensure the consolidation is performed only once, in the main process
    if not app.config.get('JSON_CONSOLIDATED'):
        # Consolidate JSON files
        consolidate_json_files('app/static/json/backgrounds',
                               'app/static/json/backgrounds/background_data.json')
        consolidate_json_files('app/static/json/party_events',
                               'app/static/json/party_events/event_data.json')
        app.config['JSON_CONSOLIDATED'] = True

    # Configure CORS using allowed origins
    CORS(app, resources={r"/*": {"origins": allowed_origins}})

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'SQLALCHEMY_DATABASE_URI')

    db.init_app(app)

    # db migrate
    migrate.init_app(app, db)

    # login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # flask-assets
    compile_static_assets(app)

    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS')

    mail.init_app(app)

    # Set the session timeout to 24 hours
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

    # Initialize SocketIO with the app
    socketio.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is the primary key
        return User.query.get(int(user_id))

    # blueprint for auth routes
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth routes
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for api routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    from .socket_events import register_socket_events
    register_socket_events(socketio)

    return app


application = create_app()
