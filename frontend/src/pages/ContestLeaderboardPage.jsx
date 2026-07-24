import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import Layout from "../components/Layout";

export default function ContestLeaderboardPage() {
  const { id } = useParams();
  const [entries, setEntries] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .get(`/contests/${id}/leaderboard`)
      .then(setEntries)
      .catch((err) => setError(err.message));
  }, [id]);

  return (
    <Layout>
      <Link to={`/contests/${id}`} className="text-accent text-sm font-mono">
        &larr; back to contest
      </Link>
      <h2 className="font-display text-lg font-semibold mt-3 mb-4">Contest Leaderboard</h2>

      {error && <p className="text-wrong font-mono text-sm">{error}</p>}
      {!entries && !error && <p className="text-text-muted font-mono text-sm">Loading...</p>}
      {entries && entries.length === 0 && (
        <p className="text-text-muted font-mono text-sm">No solves yet.</p>
      )}

      {entries && entries.length > 0 && (
        <div className="border border-border rounded-lg overflow-hidden">
          {entries.map((entry, i) => (
            <div
              key={entry.username}
              className="flex items-center justify-between px-4 py-3 border-b border-border last:border-b-0 bg-surface"
            >
              <div className="flex items-center gap-4">
                <span className="text-text-muted font-mono text-sm w-6">{i + 1}</span>
                <span className="font-medium">{entry.username}</span>
              </div>
              <span className="font-mono text-accepted text-sm">{entry.solved_count} solved</span>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
