import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Layout from "../components/Layout";

export default function ProblemListPage() {
  const [problems, setProblems] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .get("/problems")
      .then(setProblems)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Layout>
      <h2 className="font-display text-lg font-semibold mb-4">Problems</h2>

      {error && <p className="text-wrong font-mono text-sm">{error}</p>}
      {!problems && !error && <p className="text-text-muted font-mono text-sm">Loading...</p>}
      {problems && problems.length === 0 && (
        <p className="text-text-muted font-mono text-sm">No problems yet.</p>
      )}

      {problems && problems.length > 0 && (
        <ul className="space-y-2">
          {problems.map((p) => (
            <li key={p.id}>
              <Link
                to={`/problems/${p.slug}`}
                className="block bg-surface border border-border rounded-lg px-4 py-3 hover:border-accent transition-colors"
              >
                <span className="font-medium">{p.title}</span>
                <span className="text-text-muted font-mono text-xs ml-3">v{p.version}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Layout>
  );
}
