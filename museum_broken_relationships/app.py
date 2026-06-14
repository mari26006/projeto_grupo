import os

from flask import Flask, jsonify, redirect, request, url_for
from flask_login import LoginManager

from controllers import main_controller
from models.game_model import get_login_user, init_db


login_manager = LoginManager()
login_manager.login_view = 'main.login'


@login_manager.user_loader
def load_user(user_id):
    return get_login_user(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith('/api/'):
        return jsonify({'erro': 'Não autenticado'}), 401
    return redirect(url_for('main.login', next=request.url))


def create_app(test_config=None):
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'daw2026secretkey'),
        DEBUG=os.environ.get('FLASK_DEBUG') == '1',
    )

    if test_config:
        app.config.update(test_config)

    login_manager.init_app(app)
    app.register_blueprint(main_controller)
    init_db()
    return app


app = create_app()


if __name__ == '__main__':
    app.run()
