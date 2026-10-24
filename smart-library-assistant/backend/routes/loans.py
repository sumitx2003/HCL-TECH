
from datetime import datetime, timedelta, timezone
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from backend.routes.users import get_current_user
from backend.database import get_connection

router = APIRouter(prefix="/loans", tags=["Book Loans"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("/borrow/{book_id}", status_code=status.HTTP_201_CREATED)
def borrow_book(book_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        book = conn.execute(
            """
            SELECT id, title, available_copies
            FROM books
            WHERE id = ?
            """,
            (book_id,),
        ).fetchone()

        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")

        if book["available_copies"] <= 0:
            raise HTTPException(
                status_code=409,
                detail="No copies of this book are currently available",
            )

        existing_loan = conn.execute(
            """
            SELECT id FROM loans
            WHERE user_id = ? AND book_id = ? AND status = 'active'
            """,
            (current_user["id"], book_id),
        ).fetchone()

        if existing_loan:
            raise HTTPException(
                status_code=409,
                detail="You already have an active loan for this book",
            )

        borrowed_at = utc_now()
        due_at = borrowed_at + timedelta(days=14)

        # This prototype treats self-service issuance as issued by
        # the authenticated user, satisfying the existing FK constraint.
        cursor = conn.execute(
            """
            INSERT INTO loans
                (user_id, book_id, issued_by, borrowed_at, due_at,
                 returned_at, renewal_count, status)
            VALUES (?, ?, ?, ?, ?, NULL, 0, 'active')
            """,
            (
                current_user["id"],
                book_id,
                current_user["id"],
                borrowed_at.isoformat(),
                due_at.isoformat(),
            ),
        )

        conn.execute(
            """
            UPDATE books
            SET available_copies = available_copies - 1,
                updated_at = ?
            WHERE id = ? AND available_copies > 0
            """,
            (borrowed_at.isoformat(), book_id),
        )

        conn.commit()

        return {
            "message": "Book borrowed successfully",
            "loan_id": cursor.lastrowid,
            "book_id": book_id,
            "book_title": book["title"],
            "borrowed_at": borrowed_at.isoformat(),
            "due_at": due_at.isoformat(),
        }

    except HTTPException:
        conn.rollback()
        raise
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Database constraint prevented the loan: {exc}",
        )
    finally:
        conn.close()


@router.get("/my-loans")
def get_my_loans(current_user: dict = Depends(get_current_user)):
    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                l.id AS loan_id,
                l.book_id,
                b.title,
                b.isbn,
                l.borrowed_at,
                l.due_at,
                l.returned_at,
                l.renewal_count,
                l.status
            FROM loans AS l
            JOIN books AS b ON b.id = l.book_id
            WHERE l.user_id = ?
            ORDER BY l.borrowed_at DESC
            """,
            (current_user["id"],),
        ).fetchall()

        return {"loans": [dict(row) for row in rows]}
    finally:
        conn.close()


@router.post("/return/{loan_id}")
def return_book(loan_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        loan = conn.execute(
            """
            SELECT id, book_id, status
            FROM loans
            WHERE id = ? AND user_id = ?
            """,
            (loan_id, current_user["id"]),
        ).fetchone()

        if loan is None:
            raise HTTPException(
                status_code=404,
                detail="Loan not found for your account",
            )

        if loan["status"] != "active":
            raise HTTPException(
                status_code=409,
                detail="This loan has already been returned or is not active",
            )

        returned_at = utc_now().isoformat()

        conn.execute(
            """
            UPDATE loans
            SET status = 'returned', returned_at = ?
            WHERE id = ? AND status = 'active'
            """,
            (returned_at, loan_id),
        )

        conn.execute(
            """
            UPDATE books
            SET available_copies = MIN(total_copies, available_copies + 1),
                updated_at = ?
            WHERE id = ?
            """,
            (returned_at, loan["book_id"]),
        )

        conn.commit()

        return {
            "message": "Book returned successfully",
            "loan_id": loan_id,
            "returned_at": returned_at,
        }

    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()
