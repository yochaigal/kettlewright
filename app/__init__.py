from flask import Flask
from flask_migrate import Migrate
from app.models import db
from flask_login import LoginManager
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
from .assets import compile_static_assets
import os
from .parse_json import consolidate_json_files
from dotenv import load_dotenv

migrate = Migrate()
mail = Mail()
socketio = SocketIO()

def create_app():
    load_dotenv('../env')

    base_dir = os.path.abspath(os.path.dirname(__file__))

    consolidate_json_files(
        os.path.join(base_dir, 'static/json/backgrounds'),
        os.path.join(base_dir, 'static/json/backgrounds/background_data.json')
    )

    consolidate_json_files(
        os.path.join(base_dir, 'static/json/party_events'),
        os.path.join(base_dir, 'static/json/party_events/event_data.json')
    )

    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise ValueError("No SECRET_KEY set for Flask application")

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("No SQLALCHEMY_DATABASE_URI set for Flask application")

    db.init_app(app)

    # Initialize Flask-Migrate
    migrate.init_app(app, db)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Compile static assets
    compile_static_assets(app)

    # Flask-Mail configurations
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS')

    mail.init_app(app)

    # Initialize Flask-SocketIO
    socketio.init_app(app)

    # Load user from the database
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is the primary key
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Register socket events
    from .socket_events import register_socket_events
    register_socket_events(socketio)

    return app

# Create the application instance
application = create_app()

if __name__ == '__main__':
    socketio.run(application)

