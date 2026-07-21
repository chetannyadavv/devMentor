import { useEffect, useState } from "react";
import { api } from "../api/client";
import Layout from "../components/Layout";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .get("/leaderboard")
      .then(setEntries)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Layout>
      <h2 className="font-display text-lg font-semibold mb-4">Leaderboard</h2>

      {error && <p className="text-wrong font-mono text-sm">{error}</p>}
      {!entries && !error && <p className="text-text-muted font-mono text-sm">Loading...</p>}
      {entries && entries.length === 0 && (
        <p className="text-text-muted font-mono text-sm">
          No one's solved a problem yet -- be the first.
        </p>
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
              <span className="font-mono text-accepted text-sm">
                {entry.solved_count} solved
              </span>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
