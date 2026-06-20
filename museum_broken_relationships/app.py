import os

from flask import Flask
from flask_login import LoginManager

import settings
from controllers import main_controller as views
from models.game_model import Database, get_user


login_manager = LoginManager()
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)


def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)

    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    db = Database(os.path.join(models_dir, "game.sqlite"))
    app.config["db"] = db

    login_manager.init_app(app)

    app.add_url_rule("/", view_func=views.index)
    app.add_url_rule("/register", view_func=views.register, methods=["GET", "POST"])
    app.add_url_rule("/login", view_func=views.login, methods=["GET", "POST"])
    app.add_url_rule("/logout", view_func=views.logout)
    app.add_url_rule("/dashboard", view_func=views.dashboard)
    app.add_url_rule("/construir", view_func=views.construir, methods=["POST"])
    app.add_url_rule("/dar-ordem", view_func=views.dar_ordem, methods=["POST"])
    app.add_url_rule("/recolher", view_func=views.recolher, methods=["POST"])
    app.add_url_rule("/reiniciar", view_func=views.reiniciar, methods=["POST"])
    app.add_url_rule("/api/construir", view_func=views.api_construir, methods=["POST"])
    app.add_url_rule("/api/dar_ordem", view_func=views.api_dar_ordem, methods=["POST"])
    app.add_url_rule("/api/recolher", view_func=views.api_recolher, methods=["POST"])
    app.add_url_rule("/api/estado", view_func=views.api_estado)
    app.add_url_rule("/api/verificar_tarefa", view_func=views.api_verificar_tarefa, methods=["POST"])

    return app


app = create_app()


if __name__ == "__main__":
    port = app.config.get("PORT", 8080)
    app.run(host="0.0.0.0", port=port)
