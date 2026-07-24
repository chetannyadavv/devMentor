import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import Layout from "../components/Layout";

const STATUS_COLOR = {
  upcoming: "text-tle",
  active: "text-accepted",
  ended: "text-text-muted",
};

export default function ContestDetailPage() {
  const { id } = useParams();
  const [contest, setContest] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setContest(null);
    setError(null);
    api.get(`/contests/${id}`).then(setContest).catch((err) => setError(err.message));
  }, [id]);

  if (error) {
    return (
      <Layout>
        <p className="text-wrong font-mono text-sm">{error}</p>
      </Layout>
    );
  }

  if (!contest) {
    return (
      <Layout>
        <p className="text-text-muted font-mono text-sm">Loading...</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <Link to="/contests" className="text-accent text-sm font-mono">
        &larr; back to contests
      </Link>

      <div className="flex items-center justify-between mt-3 mb-1">
        <h2 className="font-display text-2xl font-bold">{contest.title}</h2>
        <span className={`font-mono text-xs uppercase ${STATUS_COLOR[contest.status] ?? "text-text"}`}>
          {contest.status}
        </span>
      </div>
      <p className="text-text-muted font-mono text-xs mb-6">
        {new Date(contest.start_time).toLocaleString()} &rarr;{" "}
        {new Date(contest.end_time).toLocaleString()}
      </p>

      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-sm font-semibold text-text-muted uppercase tracking-wide">
          Problems
        </h3>
        <Link to={`/contests/${id}/leaderboard`} className="text-accent text-sm font-mono">
          View leaderboard &rarr;
        </Link>
      </div>

      {contest.status === "upcoming" && (
        <p className="text-text-muted font-mono text-sm mb-3">
          Problems will be revealed when the contest starts.
        </p>
      )}

      <div className="space-y-2">
        {contest.problems.map((p) => (
          <Link
            key={p.id}
            to={`/problems/${p.slug}`}
            className="block bg-surface border border-border rounded-lg px-4 py-3 hover:border-accent transition-colors"
          >
            {p.title}
          </Link>
        ))}
      </div>
    </Layout>
  );
}
