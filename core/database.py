import os
from sqlmodel import SQLModel, Session, create_engine


def _build_database_url() -> str:
    url = os.getenv("DATABASE_URL", "")

    # Railway sets individual Postgres vars — build URL from them as fallback
    if not url or url == "sqlite:///./tax_prep.db":
        pghost = os.getenv("PGHOST")
        if pghost:
            pguser = os.getenv("PGUSER", "postgres")
            pgpass = os.getenv("PGPASSWORD", "")
            pgport = os.getenv("PGPORT", "5432")
            pgdb = os.getenv("PGDATABASE", "railway")
            return f"postgresql://{pguser}:{pgpass}@{pghost}:{pgport}/{pgdb}"

    if not url:
        return "sqlite:///./tax_prep.db"

    # Strip whitespace and quotes
    url = url.strip().strip('"').strip("'")

    # Railway uses "postgres://" but SQLAlchemy requires "postgresql://"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


DATABASE_URL = _build_database_url()
print(f"[database] Using: {DATABASE_URL[:20]}...")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args, pool_pre_ping=True)


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
