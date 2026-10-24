
from fastapi import APIRouter, HTTPException, Query
from backend.database import get_connection
from backend.models import BookCreate, BookUpdate

router = APIRouter(prefix="/books", tags=["Books"])


# Create a new book
@router.post("/", status_code=201)
def create_book(book: BookCreate):
    data = book.model_dump()

    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO books (
                    isbn, title, description, publisher,
                    publication_year, edition, language,
                    cover_image_url, total_copies, available_copies
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["isbn"],
                    data["title"],
                    data["description"],
                    data["publisher"],
                    data["publication_year"],
                    data["edition"],
                    data["language"],
                    data["cover_image_url"],
                    data["total_copies"],
                    data["available_copies"],
                ),
            )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM books WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

            return dict(row)

        except Exception as exc:
            conn.rollback()

            if "UNIQUE constraint failed" in str(exc):
                raise HTTPException(
                    status_code=409,
                    detail="This ISBN already exists",
                ) from exc

            raise


# List all books or search by title, ISBN, or publisher
@router.get("/")
def list_books(
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    with get_connection() as conn:
        if q:
            search = f"%{q}%"
            rows = conn.execute(
                """
                SELECT * FROM books
                WHERE title LIKE ?
                   OR isbn LIKE ?
                   OR publisher LIKE ?
                ORDER BY title
                LIMIT ? OFFSET ?
                """,
                (search, search, search, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM books
                ORDER BY title
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        return [dict(row) for row in rows]


# Get a single book by ID
@router.get("/{book_id}")
def get_book(book_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    return dict(row)


# Update an existing book
@router.patch("/{book_id}")
def update_book(book_id: int, book: BookUpdate):
    changes = book.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=400,
            detail="No fields provided to update",
        )

    with get_connection() as conn:
        current = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()

        if current is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found",
            )

        total = changes.get(
            "total_copies", current["total_copies"]
        )
        available = changes.get(
            "available_copies", current["available_copies"]
        )

        if total is None or available is None or available > total:
            raise HTTPException(
                status_code=400,
                detail="Available copies cannot exceed total copies",
            )

        # Validate copy counts and prevent invalid inventory changes.
        if (
            "total_copies" in changes
            and "available_copies" not in changes
        ):
            difference = total - current["total_copies"]
            changes["available_copies"] = (
                current["available_copies"] + difference
            )

            if changes["available_copies"] < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Total copies cannot be reduced below currently unavailable copies",
                )

        if changes.get("available_copies", available) > total:
            raise HTTPException(
                status_code=400,
                detail="Available copies cannot exceed total copies",
            )

        assignments = ", ".join(
            f"{field} = ?" for field in changes
        )
        values = list(changes.values())
        values.append(book_id)

        try:
            conn.execute(
                f"""
                UPDATE books
                SET {assignments},
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                values,
            )
            conn.commit()

        except Exception as exc:
            conn.rollback()

            if "UNIQUE constraint failed" in str(exc):
                raise HTTPException(
                    status_code=409,
                    detail="This ISBN already exists",
                ) from exc

            raise

        updated = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()

        return dict(updated)


# Delete a book
@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int):
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                "DELETE FROM books WHERE id = ?",
                (book_id,),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Book not found",
                )

            conn.commit()

        except HTTPException:
            raise

        except Exception as exc:
            conn.rollback()

            if "FOREIGN KEY constraint failed" in str(exc):
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete a book referenced by loans or reservations",
                ) from exc

            raise
