from flask import Flask
from flask_migrate import Migrate
from app.models import db
from flask_login import LoginManager
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from .assets import compile_static_assets
import os
from .parse_json import consolidate_json_files

migrate = Migrate()
mail = Mail()


def create_app():
    # create consolidated backgrounds json file
    consolidate_json_files('app/static/json/backgrounds',
                           'app/static/json/backgrounds/background_data.json')

    # create consolidated events json file
    consolidate_json_files('app/static/json/party_events',
                           'app/static/json/party_events/event_data.json')

    app = Flask(__name__)

    # Configure CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'SQLALCHEMY_DATABASE_URI')

    db.init_app(app)

    # flask-migrate
    migrate.init_app(app, db)

    # flask-login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # flask-assets, configured in assets.py
    compile_static_assets(app)

    # Flask-Mail configurations
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS')

    mail.init_app(app)

    socketio = SocketIO(app, async_mode='eventlet',
                        manage_session=False, cors_allowed_origins='*')

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

    from .socket_events import register_socket_events
    register_socket_events(socketio)

    return app


application = create_app()
