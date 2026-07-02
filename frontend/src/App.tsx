import { FormEvent, useEffect, useState } from "react";
import {
  askQuestion,
  ChatResponse,
  fetchKnowledgeBases,
  KnowledgeBase,
  login,
  uploadDocument,
} from "./api";

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [email, setEmail] = useState("admin@local");
  const [password, setPassword] = useState("admin123!");
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    fetchKnowledgeBases(token)
      .then((items) => {
        setKnowledgeBases(items);
        if (items.length > 0) {
          setSelectedKb(items[0].id);
        }
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const accessToken = await login(email, password);
      localStorage.setItem("token", accessToken);
      setToken(accessToken);
    } catch {
      setError("Invalid credentials");
    }
  }

  async function handleAsk(event: FormEvent) {
    event.preventDefault();
    if (!token || !selectedKb || !question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await askQuestion(token, selectedKb, question.trim());
      setAnswer(response);
    } catch {
      setError("Failed to get an answer");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!token || !selectedKb || !file) return;
    setError(null);
    try {
      await uploadDocument(token, selectedKb, file);
      alert(`Uploaded ${file.name} for indexing`);
    } catch {
      setError("Upload failed");
    }
  }

  if (!token) {
    return (
      <main className="page">
        <section className="card">
          <h1>Enterprise RAG</h1>
          <p>Sign in to query department knowledge bases.</p>
          <form onSubmit={handleLogin} className="stack">
            <label>
              Email
              <input value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <button type="submit">Sign in</button>
          </form>
          {error && <p className="error">{error}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="header">
        <div>
          <h1>Enterprise RAG</h1>
          <p>Hybrid search, reranking, and cited answers.</p>
        </div>
        <button
          onClick={() => {
            localStorage.removeItem("token");
            setToken(null);
          }}
        >
          Sign out
        </button>
      </header>

      <section className="grid">
        <div className="card stack">
          <label>
            Knowledge base
            <select value={selectedKb} onChange={(e) => setSelectedKb(e.target.value)}>
              {knowledgeBases.map((kb) => (
                <option key={kb.id} value={kb.id}>
                  {kb.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Upload document
            <input type="file" onChange={handleUpload} />
          </label>

          <form onSubmit={handleAsk} className="stack">
            <label>
              Question
              <textarea
                rows={5}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about SOPs, manuals, policies..."
              />
            </label>
            <button type="submit" disabled={loading}>
              {loading ? "Searching..." : "Ask"}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </div>

        <div className="card stack">
          <h2>Answer</h2>
          {answer ? (
            <>
              <article className="answer">{answer.answer}</article>
              <div>
                <h3>Citations</h3>
                <ul className="citations">
                  {answer.citations.map((citation, index) => (
                    <li key={`${citation.document_id}-${citation.chunk_index}-${index}`}>
                      <strong>{citation.filename}</strong>
                      <span> chunk {citation.chunk_index}</span>
                      <p>{citation.snippet}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <p className="muted">Ask a question to retrieve grounded answers with sources.</p>
          )}
        </div>
      </section>
    </main>
  );
}
