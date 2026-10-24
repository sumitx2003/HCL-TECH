
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "library.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection():
    """Create a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(
        DB_PATH,
        timeout=10,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create all tables and indexes defined in schema.sql."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    try:
        with get_connection() as conn:
            conn.executescript(schema)

            # Verify that the expected tables exist.
            rows = conn.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """).fetchall()

            table_names = [row["name"] for row in rows]

            print("SQLite database initialized successfully!")
            print(f"Database location: {DB_PATH}")
            print("\nTables created:")
            for name in table_names:
                print(f"  - {name}")

    except sqlite3.Error as error:
        raise RuntimeError(
            f"Database initialization failed: {error}"
        ) from error


if __name__ == "__main__":
    initialize_database()
