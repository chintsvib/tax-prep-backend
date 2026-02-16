import os
from sqlalchemy import text, inspect
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


def _migrate_columns():
    """Add any missing columns to existing tables (lightweight auto-migration)."""

    inspector = inspect(engine)
    for table_name, table in SQLModel.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue  # Table doesn't exist yet — create_all will handle it
        existing = {col["name"] for col in inspector.get_columns(table_name)}
        with engine.begin() as conn:
            for col in table.columns:
                if col.name not in existing:
                    col_type = col.type.compile(engine.dialect)
                    default = ""
                    if col.default is not None:
                        default = f" DEFAULT {col.default.arg!r}"
                    elif col.nullable:
                        default = " DEFAULT NULL"
                    elif str(col_type) in ("FLOAT", "DOUBLE PRECISION", "REAL"):
                        default = " DEFAULT 0.0"
                    elif str(col_type) in ("INTEGER", "BIGINT", "SMALLINT"):
                        default = " DEFAULT 0"
                    elif "VARCHAR" in str(col_type) or "TEXT" in str(col_type):
                        default = " DEFAULT ''"
                    null = "" if col.nullable else " NOT NULL"
                    sql = f'ALTER TABLE {table_name} ADD COLUMN "{col.name}" {col_type}{null}{default}'
                    print(f"[migrate] {sql}")
                    conn.execute(text(sql))


def create_db():
    _migrate_columns()
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
