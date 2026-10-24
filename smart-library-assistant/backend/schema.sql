
PRAGMA foreign_keys = ON;

-- 1. USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student'
        CHECK (role IN ('student', 'faculty', 'librarian', 'admin')),
    course TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- 2. BOOKS
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    publisher TEXT,
    publication_year INTEGER,
    edition TEXT,
    language TEXT DEFAULT 'English',
    cover_image_url TEXT,

    total_copies INTEGER NOT NULL DEFAULT 1
        CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL DEFAULT 1
        CHECK (
            available_copies >= 0
            AND available_copies <= total_copies
        ),

    created_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- 3. AUTHORS
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 4. BOOK-AUTHOR RELATIONSHIP
CREATE TABLE IF NOT EXISTS book_authors (
    book_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    author_order INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id)
        ON DELETE RESTRICT
);

-- 5. LOANS
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    issued_by INTEGER NOT NULL,

    borrowed_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    due_at TEXT NOT NULL,
    returned_at TEXT,
    renewal_count INTEGER NOT NULL DEFAULT 0
        CHECK (renewal_count >= 0),

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'returned', 'lost')),

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT,
    FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE RESTRICT,
    FOREIGN KEY (issued_by) REFERENCES users(id)
        ON DELETE RESTRICT,

    CHECK (due_at > borrowed_at),
    CHECK (
        (status = 'active' AND returned_at IS NULL)
        OR (status = 'returned' AND returned_at IS NOT NULL)
        OR status = 'lost'
    )
);

CREATE INDEX IF NOT EXISTS idx_loans_user_status
ON loans(user_id, status);

CREATE INDEX IF NOT EXISTS idx_loans_due_date
ON loans(due_at) WHERE status = 'active';

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_loan
ON loans(user_id, book_id) WHERE status = 'active';

-- 6. RESERVATIONS
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    queue_position INTEGER,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending', 'ready', 'fulfilled', 'cancelled', 'expired'
        )),

    created_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    expires_at TEXT,
    fulfilled_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT,
    FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_reservations_queue
ON reservations(book_id, status, queue_position);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_live_reservation
ON reservations(user_id, book_id)
WHERE status IN ('pending', 'ready');

-- 7. FINES
CREATE TABLE IF NOT EXISTS fines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount_paise INTEGER NOT NULL CHECK (amount_paise >= 0),
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unpaid'
        CHECK (status IN ('unpaid', 'paid', 'waived')),
    created_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    paid_at TEXT,

    FOREIGN KEY (loan_id) REFERENCES loans(id)
        ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT
);

-- 8. FINE PAYMENTS
CREATE TABLE IF NOT EXISTS fine_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fine_id INTEGER NOT NULL,
    amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
    payment_method TEXT NOT NULL
        CHECK (payment_method IN ('cash', 'online', 'other')),
    received_by INTEGER,
    transaction_ref TEXT UNIQUE,
    paid_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (fine_id) REFERENCES fines(id)
        ON DELETE RESTRICT,
    FOREIGN KEY (received_by) REFERENCES users(id)
        ON DELETE RESTRICT
);

-- 9. AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    outcome TEXT NOT NULL
        CHECK (outcome IN ('success', 'failure', 'denied')),
    latency_ms INTEGER CHECK (
        latency_ms IS NULL OR latency_ms >= 0
    ),
    details_json TEXT,
    created_at TEXT NOT NULL DEFAULT
        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL
);

-- 10. SEARCH INDEXES
CREATE INDEX IF NOT EXISTS idx_users_role
ON users(role);

CREATE INDEX IF NOT EXISTS idx_books_title
ON books(title COLLATE NOCASE);

CREATE INDEX IF NOT EXISTS idx_book_authors_author
ON book_authors(author_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created
ON audit_logs(created_at);
