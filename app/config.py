import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv(os.path.join(BASE_DIR, ".env"))


def _normalize_database_url(database_url: str) -> str:
    # Render's Postgres connection strings historically use the "postgres://"
    # scheme, which SQLAlchemy does not recognize. Normalize it to the
    # "postgresql://" scheme that psycopg2/SQLAlchemy accept.
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://") :]
    # Flask-SQLAlchemy 3.x also rejects "postgres://" in some versions; keep env in sync.
    if database_url != os.environ.get("DATABASE_URL", "").strip():
        os.environ["DATABASE_URL"] = database_url
    return database_url


def get_database_uri(app) -> tuple[str, bool]:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return _normalize_database_url(database_url), False

    db_path = os.path.join(app.instance_path, "sales.db")
    os.makedirs(app.instance_path, exist_ok=True)
    return f"sqlite:///{db_path}", True


def should_seed_sample_data(is_local_sqlite: bool) -> bool:
    seed_flag = os.environ.get("SEED_SAMPLE_DATA", "").strip().lower()
    if seed_flag in {"1", "true", "yes"}:
        return True
    if seed_flag in {"0", "false", "no"}:
        return False
    return is_local_sqlite


def get_database_label(database_uri: str) -> str:
    if database_uri.startswith("sqlite:"):
        return "Local SQLite"
    if "mysql" in database_uri or "mariadb" in database_uri:
        return "Live MySQL"
    if "postgresql" in database_uri or "postgres" in database_uri:
        return "Live PostgreSQL"
    if "mssql" in database_uri:
        return "Live SQL Server"
    return "Live SQL Database"
