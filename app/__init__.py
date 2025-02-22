import os
import logging
from flask import Flask, request
from flask_migrate import Migrate
from app.models import db
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_cors import CORS
from .assets import compile_static_assets
from app.lib import consolidate_json_files
from datetime import datetime, timezone
from datetime import timedelta
from flask_babel import Babel
from flask_babel import _
import urllib.parse

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

# Determine locale
def get_locale():
    lang = request.args.get('lang')
    if lang != None and lang != "":
        return lang    
    lang = request.cookies.get('kw_lang')
    if lang != None and lang != "":
        return lang
    return "en"
    
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

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is the primary key
        return User.query.get(int(user_id))

    # blueprint for auth routes
    from app.blueprints import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth routes
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for api routes
    from app.blueprints import api as api_blueprint
    app.register_blueprint(api_blueprint)
    
    # blueprint for partial character editors
    from app.blueprints import character_edit as character_edit_blueprint
    app.register_blueprint(character_edit_blueprint)
    
    # blueprint for marketplace dialog
    from app.blueprints import marketplace as marketplace_blueprint
    app.register_blueprint(marketplace_blueprint)
    
    # blueprint for party page
    from app.blueprints import party as party_blueprint
    app.register_blueprint(party_blueprint)
    
    # blueprint for generator
    from app.blueprints import generator as generator_blueprint
    app.register_blueprint(generator_blueprint)
    
    # blueprint for character creation
    from app.blueprints import character_create as character_create_blueprint
    app.register_blueprint(character_create_blueprint)

    from .socket_events import register_socket_events
    register_socket_events(socketio)
    
    # Convert end of line chars into HTML <br>
    @app.template_filter("eol2br")
    def eol2br_filter(text: str) -> str:
        return text.replace("\n","<br/>")
    
    # Sanitize single quote for JS calls
    @app.template_filter("squote2js")
    def squote2js_filter(text: str) -> str:
        return text.replace("'","’")
    
    # Translate
    @app.template_filter("tr")
    def squote2js_filter(text: str) -> str:
        return _(text)
    
    # URL decode
    @app.template_filter("urldec")
    def urlenc_filter(text: str) -> str:
        return urllib.parse.unquote_plus(text)
    
    # Truncate text to 36 chars
    @app.template_filter("trunc36")
    def urlenc_filter(text: str) -> str:
        return text[0:36]
    
    # Write error about party code
    @app.template_filter("party_code_error")
    def party_code_error_filter(text: str) -> str:
        if text == None:
            return None
        if text.startswith('Invalid last party code:'):
            return text
        return None
    
    @app.context_processor
    def inject_locale():
        return dict(locale=get_locale())

    return app




application = create_app()
babel = Babel(application, locale_selector=get_locale)