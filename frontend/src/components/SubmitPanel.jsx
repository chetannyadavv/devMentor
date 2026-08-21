import { useState, useRef, useEffect } from "react";
import Editor from "@monaco-editor/react";
import { api, submissionWsUrl } from "../api/client";

const LANGUAGES = [
  { value: "python", label: "Python", monaco: "python" },
  { value: "cpp", label: "C++", monaco: "cpp" },
  { value: "java", label: "Java", monaco: "java" },
];

const STARTER_CODE = {
  python: "# write your solution here\n",
  cpp: "#include <iostream>\nint main() {\n    \n    return 0;\n}\n",
  java: "public class Solution {\n    public static void main(String[] args) {\n        \n    }\n}\n",
};

const VERDICT_COLOR = {
  ACCEPTED: "text-accepted",
  WRONG_ANSWER: "text-wrong",
  TIME_LIMIT_EXCEEDED: "text-tle",
  COMPILE_ERROR: "text-compile-error",
  RUNTIME_ERROR: "text-runtime-error",
  FAILED: "text-wrong", // overall verdict when any test case didn't pass
};

export default function SubmitPanel({ problemSlug }) {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(STARTER_CODE.python);
  const [status, setStatus] = useState("idle"); // idle | judging | done
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  function handleLanguageChange(lang) {
    setLanguage(lang);
    setCode(STARTER_CODE[lang]);
  }

  function pollAiFeedback(submissionId) {
    const interval = setInterval(async () => {
      try {
        const full = await api.get(`/submissions/${submissionId}`);
        if (full.ai_feedback_status === "ready" || full.ai_feedback_status === "unavailable") {
          setResult(full);
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
      }
    }, 3000);
    // Stop polling after a reasonable ceiling, in case something hangs
    // -- feedback is a nice-to-have, never something worth polling
    // forever over.
    setTimeout(() => clearInterval(interval), 60000);
  }

  async function handleSubmit() {
    setError(null);
    setResult(null);
    setStatus("judging");

    try {
      const submission = await api.post("/submissions", {
        problem_slug: problemSlug,
        language,
        source_code: code,
      });

      const ws = new WebSocket(submissionWsUrl(submission.id));
      wsRef.current = ws;

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        // The push only carries the overall verdict -- fetch the full
        // per-test-case breakdown once we know it's actually done.
        const full = await api.get(`/submissions/${submission.id}`);
        setResult(full);
        setStatus("done");
        ws.close();
        pollAiFeedback(submission.id);
      };

      ws.onerror = () => {
        setError("Lost connection while waiting for the verdict.");
        setStatus("idle");
      };
    } catch (err) {
      setError(err.message);
      setStatus("idle");
    }
  }

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-3">
        <select
          value={language}
          onChange={(e) => handleLanguageChange(e.target.value)}
          className="bg-surface border border-border rounded px-3 py-1.5 text-sm font-mono outline-none focus:border-accent"
        >
          {LANGUAGES.map((l) => (
            <option key={l.value} value={l.value}>
              {l.label}
            </option>
          ))}
        </select>

        <button
          onClick={handleSubmit}
          disabled={status === "judging"}
          className="bg-accent text-bg font-medium rounded px-4 py-1.5 text-sm disabled:opacity-50"
        >
          {status === "judging" ? "Judging..." : "Submit"}
        </button>
      </div>

      <div className="border border-border rounded-lg overflow-hidden">
        <Editor
          height="360px"
          language={LANGUAGES.find((l) => l.value === language).monaco}
          value={code}
          onChange={(value) => setCode(value ?? "")}
          theme="vs-dark"
          options={{ fontSize: 13, minimap: { enabled: false } }}
        />
      </div>

      {error && <p className="text-wrong font-mono text-sm mt-4">{error}</p>}

      {status === "judging" && (
        <p className="text-text-muted font-mono text-sm mt-4 animate-pulse">
          Running your code in the sandbox...
        </p>
      )}

      {result && (
        <div className="mt-4">
          <p className={`font-display text-lg font-bold ${VERDICT_COLOR[result.overall_verdict] ?? "text-text"}`}>
            {result.overall_verdict}
          </p>
          <div className="mt-3 space-y-2">
            {result.test_case_results.map((tc) => (
              <div
                key={tc.test_case_index}
                className="bg-surface border border-border rounded px-3 py-2 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-text-muted">
                    Test {tc.test_case_index + 1}
                  </span>
                  <span className={`font-mono font-medium ${VERDICT_COLOR[tc.verdict] ?? "text-text"}`}>
                    {tc.verdict}
                  </span>
                  <span className="font-mono text-text-muted text-xs">
                    {tc.runtime_seconds}s
                  </span>
                </div>
                {tc.verdict !== "ACCEPTED" && tc.stdout && (
                  <div className="mt-2 pt-2 border-t border-border">
                    <span className="text-text-muted text-xs">Your output</span>
                    <pre className="text-text text-xs font-mono whitespace-pre-wrap mt-1">
                      {tc.stdout}
                    </pre>
                  </div>
                )}
                {tc.verdict !== "ACCEPTED" && tc.stderr && (
                  <div className="mt-2 pt-2 border-t border-border">
                    <span className="text-text-muted text-xs">Error</span>
                    <pre className="text-runtime-error text-xs font-mono whitespace-pre-wrap mt-1">
                      {tc.stderr}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>

          {result.ai_feedback_status === "ready" && (
            <div className="mt-4 bg-surface border border-accent/40 rounded-lg p-4">
              <span className="text-accent text-xs font-mono uppercase tracking-wide">
                AI Mentor
              </span>
              <p className="text-text text-sm mt-2 leading-relaxed">{result.ai_feedback_text}</p>
            </div>
          )}
          {result.ai_feedback_status === "pending" && (
            <p className="text-text-muted font-mono text-xs mt-4 animate-pulse">
              Generating feedback...
            </p>
          )}
          {result.ai_feedback_status === "unavailable" && (
            <p className="text-text-muted font-mono text-xs mt-4">
              AI feedback isn't available for this submission right now.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
