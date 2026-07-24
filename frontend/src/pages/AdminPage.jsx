import { useEffect, useState } from "react";
import { api } from "../api/client";
import Layout from "../components/Layout";

function Section({ title, children }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-6 mb-6">
      <h3 className="font-display text-sm font-semibold text-text-muted uppercase tracking-wide mb-4">
        {title}
      </h3>
      {children}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div className="mb-4">
      <label className="block text-sm text-text-muted mb-1">{label}</label>
      {children}
    </div>
  );
}

const inputClass =
  "w-full bg-bg border border-border rounded px-3 py-2 font-mono text-sm outline-none focus:border-accent";

function Message({ text, isError }) {
  if (!text) return null;
  return (
    <p className={`font-mono text-sm mt-3 ${isError ? "text-wrong" : "text-accepted"}`}>{text}</p>
  );
}

export default function AdminPage() {
  const [problems, setProblems] = useState([]);

  const refreshProblems = () => {
    api.get("/problems").then(setProblems).catch(() => {});
  };

  useEffect(refreshProblems, []);

  // --- Create Problem ---
  const [pSlug, setPSlug] = useState("");
  const [pTitle, setPTitle] = useState("");
  const [pStatement, setPStatement] = useState("");
  const [pMsg, setPMsg] = useState(null);

  async function handleCreateProblem(e) {
    e.preventDefault();
    setPMsg(null);
    try {
      await api.post("/problems", { slug: pSlug, title: pTitle, statement: pStatement });
      setPMsg({ text: `Created "${pTitle}"`, isError: false });
      setPSlug("");
      setPTitle("");
      setPStatement("");
      refreshProblems();
    } catch (err) {
      setPMsg({ text: err.message, isError: true });
    }
  }

  // --- Add Test Case ---
  const [tcSlug, setTcSlug] = useState("");
  const [tcStdin, setTcStdin] = useState("");
  const [tcExpected, setTcExpected] = useState("");
  const [tcSample, setTcSample] = useState(false);
  const [tcMsg, setTcMsg] = useState(null);

  async function handleAddTestCase(e) {
    e.preventDefault();
    setTcMsg(null);
    try {
      await api.post(`/problems/${tcSlug}/test-cases`, {
        stdin: tcStdin,
        expected_output: tcExpected,
        is_sample: tcSample,
      });
      setTcMsg({ text: `Test case added to "${tcSlug}"`, isError: false });
      setTcStdin("");
      setTcExpected("");
      setTcSample(false);
      refreshProblems(); // picks up the version bump
    } catch (err) {
      setTcMsg({ text: err.message, isError: true });
    }
  }

  // --- Create Contest ---
  const [cTitle, setCTitle] = useState("");
  const [cStart, setCStart] = useState("");
  const [cEnd, setCEnd] = useState("");
  const [cSelected, setCSelected] = useState(new Set());
  const [cMsg, setCMsg] = useState(null);

  function toggleProblem(slug) {
    setCSelected((prev) => {
      const next = new Set(prev);
      next.has(slug) ? next.delete(slug) : next.add(slug);
      return next;
    });
  }

  async function handleCreateContest(e) {
    e.preventDefault();
    setCMsg(null);
    try {
      await api.post("/contests", {
        title: cTitle,
        start_time: new Date(cStart).toISOString(),
        end_time: new Date(cEnd).toISOString(),
        problem_slugs: Array.from(cSelected),
      });
      setCMsg({ text: `Created "${cTitle}"`, isError: false });
      setCTitle("");
      setCStart("");
      setCEnd("");
      setCSelected(new Set());
    } catch (err) {
      setCMsg({ text: err.message, isError: true });
    }
  }

  return (
    <Layout>
      <h2 className="font-display text-lg font-semibold mb-6">Admin</h2>

      <Section title="Create Problem">
        <form onSubmit={handleCreateProblem}>
          <Field label="Slug">
            <input className={inputClass} value={pSlug} onChange={(e) => setPSlug(e.target.value)} required />
          </Field>
          <Field label="Title">
            <input className={inputClass} value={pTitle} onChange={(e) => setPTitle(e.target.value)} required />
          </Field>
          <Field label="Statement">
            <textarea
              className={inputClass}
              rows={4}
              value={pStatement}
              onChange={(e) => setPStatement(e.target.value)}
              required
            />
          </Field>
          <button type="submit" className="bg-accent text-bg font-medium rounded px-4 py-2 text-sm">
            Create Problem
          </button>
          <Message text={pMsg?.text} isError={pMsg?.isError} />
        </form>
      </Section>

      <Section title="Add Test Case">
        <form onSubmit={handleAddTestCase}>
          <Field label="Problem slug">
            <input className={inputClass} value={tcSlug} onChange={(e) => setTcSlug(e.target.value)} required />
          </Field>
          <Field label="stdin">
            <textarea
              className={inputClass}
              rows={2}
              value={tcStdin}
              onChange={(e) => setTcStdin(e.target.value)}
            />
          </Field>
          <Field label="Expected output">
            <textarea
              className={inputClass}
              rows={2}
              value={tcExpected}
              onChange={(e) => setTcExpected(e.target.value)}
              required
            />
          </Field>
          <label className="flex items-center gap-2 text-sm text-text-muted mb-4">
            <input type="checkbox" checked={tcSample} onChange={(e) => setTcSample(e.target.checked)} />
            Sample (visible to users)
          </label>
          <button type="submit" className="bg-accent text-bg font-medium rounded px-4 py-2 text-sm">
            Add Test Case
          </button>
          <Message text={tcMsg?.text} isError={tcMsg?.isError} />
        </form>
      </Section>

      <Section title="Create Contest">
        <form onSubmit={handleCreateContest}>
          <Field label="Title">
            <input className={inputClass} value={cTitle} onChange={(e) => setCTitle(e.target.value)} required />
          </Field>
          <Field label="Start time">
            <input
              type="datetime-local"
              className={inputClass}
              value={cStart}
              onChange={(e) => setCStart(e.target.value)}
              required
            />
          </Field>
          <Field label="End time">
            <input
              type="datetime-local"
              className={inputClass}
              value={cEnd}
              onChange={(e) => setCEnd(e.target.value)}
              required
            />
          </Field>
          <Field label="Problems">
            <div className="space-y-1">
              {problems.map((p) => (
                <label key={p.slug} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={cSelected.has(p.slug)}
                    onChange={() => toggleProblem(p.slug)}
                  />
                  {p.title}{" "}
                  <span className="text-text-muted font-mono text-xs">({p.slug})</span>
                </label>
              ))}
              {problems.length === 0 && (
                <p className="text-text-muted font-mono text-sm">No problems yet.</p>
              )}
            </div>
          </Field>
          <button type="submit" className="bg-accent text-bg font-medium rounded px-4 py-2 text-sm">
            Create Contest
          </button>
          <Message text={cMsg?.text} isError={cMsg?.isError} />
        </form>
      </Section>
    </Layout>
  );
}
