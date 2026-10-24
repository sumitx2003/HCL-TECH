
import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

const suggestions = [
  "What is the library borrowing policy?",
  "Summarize the main points of a research paper.",
  "What are the rules for book renewals and fines?",
  "Find documents related to artificial intelligence.",
];

export default function ResearchAssistant() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function askQuestion(text = question) {
    const query = text.trim();

    if (!query || loading) return;

    setError("");
    setMessages((old) => [
      ...old,
      { role: "user", content: query },
    ]);
    setQuestion("");
    setLoading(true);

    try {
      // Change "token" if your login code uses another storage key.
      const token = localStorage.getItem("token");

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token
            ? { Authorization: `Bearer ${token}` }
            : {}),
        },
        body: JSON.stringify({ question: query }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Please log in again to use the Research Assistant.");
        }

        throw new Error(
          data.detail || `Request failed (${response.status}).`
        );
      }

      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          content:
            data.answer ||
            data.response ||
            data.result ||
            "No answer was returned.",
          sources: data.sources || data.citations || [],
        },
      ]);
    } catch (err) {
      setError(
        `${err.message || "Could not connect to the server."} Check that FastAPI, the RAG pipeline, ChromaDB, and Ollama are running.`
      );
    } finally {
      setLoading(false);
    }
  }

  function clearChat() {
    if (!loading) {
      setMessages([]);
      setError("");
      setQuestion("");
    }
  }

  function sourceDetails(source, index) {
    if (typeof source === "string") {
      return { label: source, page: null };
    }

    return {
      label:
        source.source ||
        source.title ||
        source.filename ||
        `Source ${index + 1}`,
      page: source.page ?? source.page_number ?? null,
    };
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 text-slate-800 sm:px-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <div className="rounded-xl bg-indigo-100 p-3 text-indigo-700">
                <span className="text-2xl">📚</span>
              </div>
              <span className="text-sm font-semibold text-indigo-700">
                SHELFWISE
              </span>
            </div>

            <h1 className="text-3xl font-bold tracking-tight">
              Research Assistant
            </h1>
            <p className="mt-2 text-slate-500">
              Ask questions about library policies, research papers,
              and documents.
            </p>
          </div>

          <button
            onClick={clearChat}
            disabled={loading || messages.length === 0}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm hover:bg-slate-100 disabled:opacity-50"
          >
            Clear chat
          </button>
        </header>

        {messages.length === 0 ? (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 className="text-xl font-semibold">
              What would you like to explore?
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Choose a suggested question or type your own.
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {suggestions.map((item) => (
                <button
                  key={item}
                  onClick={() => askQuestion(item)}
                  disabled={loading}
                  className="rounded-xl border border-slate-200 p-4 text-left text-sm transition hover:border-indigo-400 hover:bg-indigo-50 disabled:opacity-50"
                >
                  <span className="mb-2 block text-lg">↗</span>
                  {item}
                </button>
              ))}
            </div>
          </section>
        ) : (
          <section
            className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 sm:p-8"
            aria-live="polite"
          >
            {messages.map((message, index) => (
              <article
                key={`${index}-${message.role}`}
                className={
                  message.role === "user"
                    ? "ml-6 rounded-xl bg-indigo-600 p-4 text-white sm:ml-16"
                    : "mr-4 rounded-xl bg-slate-50 p-4 sm:mr-10"
                }
              >
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide opacity-70">
                  {message.role === "user"
                    ? "You"
                    : "Research Assistant"}
                </p>

                <p className="whitespace-pre-wrap text-sm leading-7">
                  {message.content}
                </p>

                {message.sources?.length > 0 && (
                  <div className="mt-4 border-t border-slate-200 pt-3">
                    <h3 className="mb-2 text-sm font-semibold">
                      Sources
                    </h3>

                    <ul className="space-y-2">
                      {message.sources.map((source, sourceIndex) => {
                        const details = sourceDetails(
                          source,
                          sourceIndex
                        );

                        return (
                          <li
                            key={`${details.label}-${sourceIndex}`}
                            className="text-sm text-indigo-700"
                          >
                            📄 {details.label}
                            {details.page != null && (
                              <span className="ml-2 text-slate-500">
                                Page {details.page}
                              </span>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </article>
            ))}

            {loading && (
              <p className="animate-pulse text-sm text-slate-500">
                Searching documents and preparing your answer...
              </p>
            )}
          </section>
        )}

        {error && (
          <div
            role="alert"
            className="mt-4 flex items-start justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
          >
            <p>{error}</p>
            <button
              onClick={() => setError("")}
              className="font-semibold"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        <form
          className="mt-5 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"
          onSubmit={(event) => {
            event.preventDefault();
            askQuestion();
          }}
        >
          <label htmlFor="research-question" className="sr-only">
            Research question
          </label>

          <textarea
            id="research-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault();
                askQuestion();
              }
            }}
            placeholder="Ask about library policies or research..."
            rows={2}
            className="w-full resize-y border-0 p-3 outline-none focus:ring-0"
          />

          <div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-3">
            <p className="text-xs text-slate-400">
              Enter to send · Shift + Enter for a new line
            </p>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Thinking..." : "Ask question ↑"}
            </button>
          </div>
        </form>

        <p className="mt-4 text-center text-xs text-slate-400">
          Answers are based on retrieved documents. Check the cited
          sources for important information.
        </p>
      </div>
    </main>
  );
}
