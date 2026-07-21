import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import Layout from "../components/Layout";
import SubmitPanel from "../components/SubmitPanel";

export default function ProblemDetailPage() {
  const { slug } = useParams();
  const [problem, setProblem] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setProblem(null);
    setError(null);
    api
      .get(`/problems/${slug}`)
      .then(setProblem)
      .catch((err) => setError(err.message));
  }, [slug]);

  if (error) {
    return (
      <Layout>
        <p className="text-wrong font-mono text-sm">{error}</p>
      </Layout>
    );
  }

  if (!problem) {
    return (
      <Layout>
        <p className="text-text-muted font-mono text-sm">Loading...</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <Link to="/" className="text-accent text-sm font-mono">
        &larr; back to problems
      </Link>

      <h2 className="font-display text-2xl font-bold mt-3 mb-1">{problem.title}</h2>
      <p className="text-text-muted font-mono text-xs mb-6">
        {problem.slug} &middot; v{problem.version}
      </p>

      <p className="whitespace-pre-wrap leading-relaxed mb-8">{problem.statement}</p>

      {problem.sample_test_cases.length > 0 && (
        <div>
          <h3 className="font-display text-sm font-semibold text-text-muted mb-3 uppercase tracking-wide">
            Sample Test Cases
          </h3>
          <div className="space-y-3">
            {problem.sample_test_cases.map((tc) => (
              <div key={tc.id} className="bg-surface border border-border rounded-lg p-4">
                <div className="mb-2">
                  <span className="text-text-muted text-xs font-mono">Input</span>
                  <pre className="font-mono text-sm mt-1 whitespace-pre-wrap">{tc.stdin}</pre>
                </div>
                <div>
                  <span className="text-text-muted text-xs font-mono">Expected Output</span>
                  <pre className="font-mono text-sm mt-1 whitespace-pre-wrap">
                    {tc.expected_output}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <SubmitPanel problemSlug={problem.slug} />
    </Layout>
  );
}
