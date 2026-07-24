import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Layout from "../components/Layout";

const STATUS_COLOR = {
  upcoming: "text-tle",
  active: "text-accepted",
  ended: "text-text-muted",
};

export default function ContestListPage() {
  const [contests, setContests] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get("/contests").then(setContests).catch((err) => setError(err.message));
  }, []);

  return (
    <Layout>
      <h2 className="font-display text-lg font-semibold mb-4">Contests</h2>

      {error && <p className="text-wrong font-mono text-sm">{error}</p>}
      {!contests && !error && <p className="text-text-muted font-mono text-sm">Loading...</p>}
      {contests && contests.length === 0 && (
        <p className="text-text-muted font-mono text-sm">No contests yet.</p>
      )}

      {contests && contests.length > 0 && (
        <ul className="space-y-2">
          {contests.map((c) => (
            <li key={c.id}>
              <Link
                to={`/contests/${c.id}`}
                className="flex items-center justify-between bg-surface border border-border rounded-lg px-4 py-3 hover:border-accent transition-colors"
              >
                <span className="font-medium">{c.title}</span>
                <span className={`font-mono text-xs uppercase ${STATUS_COLOR[c.status] ?? "text-text"}`}>
                  {c.status}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Layout>
  );
}
