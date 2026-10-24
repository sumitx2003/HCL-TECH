
import { useEffect, useState } from "react";
import "./index.css";
import ResearchAssistant from "./components/ResearchAssistant";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [role, setRole] = useState("student");
  const [books, setBooks] = useState([]);
  const [loans, setLoans] = useState([]);
  const [token, setToken] = useState(
    () => localStorage.getItem("token") || ""
  );
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState("books");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [formMode, setFormMode] = useState("login");
  const [title, setTitle] = useState("");
  const [isbn, setIsbn] = useState("");
  const [copies, setCopies] = useState(1);

  const button =
    "rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50";
  const input =
    "w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-indigo-500";
  const card = "rounded-xl border border-slate-200 bg-white p-5";

  async function request(path, options = {}) {
    const currentToken = localStorage.getItem("token") || token;

    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(currentToken
          ? { Authorization: `Bearer ${currentToken}` }
          : {}),
        ...options.headers,
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : `Request failed (${response.status}).`
      );
    }

    return data;
  }

  async function loadBooks() {
    try {
      const data = await request("/books/");
      setBooks(Array.isArray(data) ? data : data.books || []);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function loadLoans() {
    try {
      const data = await request("/loans/my-loans");
      setLoans(data.loans || []);
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadBooks();
  }, []);

  async function authenticate(event) {
    event.preventDefault();
    setMessage("");

    try {
      const path =
        formMode === "login" ? "/auth/login" : "/auth/register";

      const body =
        formMode === "login"
          ? { email, password }
          : { full_name: name, email, password, course: "" };

      const data = await request(path, {
        method: "POST",
        body: JSON.stringify(body),
      });

      if (formMode === "register") {
        setMessage("Account created. Please log in.");
        setFormMode("login");
        return;
      }

      if (!data.access_token) {
        throw new Error("Login succeeded, but the server returned no access token.");
      }

      // Save token so ResearchAssistant.jsx can read it.
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);

      setRole(data.user?.role === "librarian" ? "librarian" : "student");
      setMessage(`Welcome, ${data.user?.full_name || "user"}!`);
      setPassword("");
      setPage("books");
      await loadBooks();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function borrowBook(bookId) {
    try {
      const data = await request(`/loans/borrow/${bookId}`, {
        method: "POST",
      });

      setMessage(data.message || "Book borrowed successfully.");
      await loadBooks();
      await loadLoans();
      setPage("loans");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function returnBook(loanId) {
    try {
      const data = await request(`/loans/return/${loanId}`, {
        method: "POST",
      });

      setMessage(data.message || "Book returned successfully.");
      await loadBooks();
      await loadLoans();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function addBook(event) {
    event.preventDefault();

    try {
      await request("/books/", {
        method: "POST",
        body: JSON.stringify({
          title,
          isbn: isbn || null,
          total_copies: Number(copies),
          available_copies: Number(copies),
        }),
      });

      setTitle("");
      setIsbn("");
      setCopies(1);
      setMessage("Book added successfully.");
      await loadBooks();
      setPage("books");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function deleteBook(bookId) {
    if (!window.confirm("Delete this book?")) return;

    try {
      await request(`/books/${bookId}`, { method: "DELETE" });
      setMessage("Book deleted.");
      await loadBooks();
    } catch (error) {
      setMessage(error.message);
    }
  }

  function logout() {
    localStorage.removeItem("token");
    setToken("");
    setRole("student");
    setLoans([]);
    setMessage("You have logged out.");
    setPage("books");
    setPassword("");
  }

  const filteredBooks = books.filter((book) =>
    `${book.title || ""} ${book.isbn || ""}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-white px-6 py-4">
        <div>
          <h1 className="text-2xl font-bold text-indigo-700">ShelfWise</h1>
          <p className="text-sm text-slate-500">Smart Library Assistant</p>
        </div>

        {token && (
          <nav className="flex flex-wrap gap-2">
            <button className={button} onClick={() => setPage("books")}>
              {role === "student" ? "Browse Books" : "Inventory"}
            </button>

            {role === "student" && (
              <button
                className={button}
                onClick={() => {
                  setPage("loans");
                  loadLoans();
                }}
              >
                My Loans
              </button>
            )}

            {role === "student" && (
              <button
                className={button}
                onClick={() => setPage("research")}
              >
                Research Assistant
              </button>
            )}

            {role === "librarian" && (
              <button className={button} onClick={() => setPage("add")}>
                Add Book
              </button>
            )}

            <button
              className="rounded-lg border px-4 py-2 text-sm"
              onClick={logout}
            >
              Logout
            </button>
          </nav>
        )}
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-5 py-8">
        {message && (
          <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-3 text-sm">
            {message}
            <button
              className="float-right font-bold"
              onClick={() => setMessage("")}
              aria-label="Dismiss message"
            >
              ×
            </button>
          </div>
        )}

        {!token ? (
          <section className={`${card} mx-auto max-w-md`}>
            <h2 className="mb-2 text-2xl font-bold">
              {formMode === "login"
                ? "Welcome back"
                : "Create student account"}
            </h2>

            <p className="mb-5 text-sm text-slate-500">
              {formMode === "login"
                ? "Log in to use your library account."
                : "Register as a student to borrow books."}
            </p>

            <form className="space-y-4" onSubmit={authenticate}>
              {formMode === "register" && (
                <input
                  className={input}
                  placeholder="Full name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              )}

              <input
                className={input}
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <input
                className={input}
                type="password"
                placeholder="Password (minimum 8 characters)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={formMode === "register" ? 8 : 1}
                required
              />

              <button className={`${button} w-full`}>
                {formMode === "login" ? "Login" : "Register"}
              </button>
            </form>

            <button
              className="mt-4 text-sm text-indigo-700"
              onClick={() =>
                setFormMode(formMode === "login" ? "register" : "login")
              }
            >
              {formMode === "login"
                ? "New student? Create an account"
                : "Already registered? Login"}
            </button>
          </section>
        ) : (
          <>
            {page !== "research" && (
              <section className="rounded-xl bg-indigo-700 p-6 text-white">
                <p className="text-sm text-indigo-200">
                  {role === "student" ? "STUDENT PORTAL" : "LIBRARIAN PORTAL"}
                </p>

                <h2 className="mt-2 text-3xl font-bold">
                  {page === "add"
                    ? "Add a Book"
                    : page === "loans"
                      ? "My Borrowed Books"
                      : role === "student"
                        ? "Find a Book"
                        : "Manage Books"}
                </h2>

                <p className="mt-2 text-sm text-indigo-100">
                  {role === "student"
                    ? "Browse books and manage your borrowed books."
                    : "Manage library inventory."}
                </p>
              </section>
            )}

            {page === "research" && role === "student" && (
              <ResearchAssistant />
            )}

            {page === "add" && role === "librarian" && (
              <section className={card}>
                <h3 className="mb-4 text-lg font-bold">Add new book</h3>

                <form className="space-y-3" onSubmit={addBook}>
                  <input
                    className={input}
                    placeholder="Book title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />

                  <input
                    className={input}
                    placeholder="ISBN (optional)"
                    value={isbn}
                    onChange={(e) => setIsbn(e.target.value)}
                  />

                  <label className="block text-sm">
                    Total copies
                    <input
                      className={`${input} mt-1`}
                      type="number"
                      min="1"
                      value={copies}
                      onChange={(e) => setCopies(e.target.value)}
                      required
                    />
                  </label>

                  <button className={button}>Save Book</button>
                </form>
              </section>
            )}

            {page === "books" && (
              <section className="space-y-4">
                <input
                  className={input}
                  placeholder="Search books by title or ISBN..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />

                {filteredBooks.length === 0 ? (
                  <div className={`${card} text-center text-slate-500`}>
                    No books found.
                  </div>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {filteredBooks.map((book) => (
                      <article key={book.id} className={card}>
                        <h3 className="text-lg font-bold">{book.title}</h3>

                        <p className="mt-1 text-sm text-slate-500">
                          ISBN: {book.isbn || "Not provided"}
                        </p>

                        <p className="mt-3 text-sm">
                          Available copies:{" "}
                          <strong>{book.available_copies}</strong>
                        </p>

                        {role === "student" ? (
                          <button
                            className={`${button} mt-4`}
                            disabled={!book.available_copies}
                            onClick={() => borrowBook(book.id)}
                          >
                            {book.available_copies > 0
                              ? "Borrow Book"
                              : "Unavailable"}
                          </button>
                        ) : (
                          <button
                            className="mt-4 rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white"
                            onClick={() => deleteBook(book.id)}
                          >
                            Delete Book
                          </button>
                        )}
                      </article>
                    ))}
                  </div>
                )}
              </section>
            )}

            {page === "loans" && role === "student" && (
              <section className="space-y-4">
                <button className={button} onClick={loadLoans}>
                  Refresh Loans
                </button>

                {loans.length === 0 ? (
                  <div className={card}>You have no borrowed books.</div>
                ) : (
                  loans.map((loan) => (
                    <article key={loan.loan_id} className={card}>
                      <h3 className="font-bold">{loan.title}</h3>

                      <p className="mt-2 text-sm text-slate-500">
                        Due: {loan.due_at || "Not specified"}
                      </p>

                      <p className="mt-1 text-sm">Status: {loan.status}</p>

                      {loan.status === "active" && (
                        <button
                          className={`${button} mt-3`}
                          onClick={() => returnBook(loan.loan_id)}
                        >
                          Return Book
                        </button>
                      )}
                    </article>
                  ))
                )}
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
