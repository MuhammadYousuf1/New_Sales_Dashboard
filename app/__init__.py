import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.config import get_database_label, get_database_uri, should_seed_sample_data

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

db = SQLAlchemy()


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )

    database_uri, is_local_sqlite = get_database_uri(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-sales-dashboard-key")
    app.config["DATABASE_LABEL"] = get_database_label(database_uri)
    app.config["IS_LOCAL_SQLITE"] = is_local_sqlite

    db.init_app(app)

    with app.app_context():
        from app import models  # noqa: F401
        from app.routes import main_bp
        from app.seed import seed_database

        db.create_all()
        if should_seed_sample_data(is_local_sqlite):
            seed_database()

    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_globals():
        return {"database_label": app.config.get("DATABASE_LABEL", "Database")}

    return app
