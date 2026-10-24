
import getpass
from pydantic import EmailStr, TypeAdapter

from backend.auth import hash_password
from backend.database import get_connection

email = str(
    TypeAdapter(EmailStr).validate_python(
        input("Librarian email: ").strip()
    )
).lower()

full_name = input("Librarian full name: ").strip()
password = getpass.getpass("Librarian password (minimum 8 characters): ")

if len(full_name) < 2:
    raise SystemExit("Name must contain at least 2 characters.")

if len(password) < 8:
    raise SystemExit("Password must contain at least 8 characters.")

conn = get_connection()

try:
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ? COLLATE NOCASE",
        (email,),
    ).fetchone()

    if existing:
        raise SystemExit(
            "That email already exists. Use a different email or update "
            "the existing account's role through an authorized process."
        )

    cursor = conn.execute(
        """
        INSERT INTO users
            (full_name, email, password_hash, role, course, is_active)
        VALUES (?, ?, ?, 'librarian', NULL, 1)
        """,
        (full_name, email, hash_password(password)),
    )

    conn.commit()
    print(f"Librarian account created. User ID: {cursor.lastrowid}")

except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
