import click
from flask import Flask

from myapp.config import Config
from myapp.extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from myapp.api.auth import api_auth_bp
    from myapp.api.forum import api_forum_bp
    from myapp.api.health import health_bp
    from myapp.web.auth import auth_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_forum_bp)
    app.register_blueprint(auth_bp)

    @app.cli.command("bot-respond")
    @click.option(
        "--delay", default=None, type=int, help="Minutos de espera antes de responder."
    )
    def bot_respond_command(delay):
        """Revisa preguntas sin respuesta y genera respuestas automáticas."""
        from myapp.services.bot_service import BotService

        count = BotService.process_unanswered_questions(delay_minutes=delay)
        click.echo(f"Preguntas respondidas por el bot: {count}")

    return app
