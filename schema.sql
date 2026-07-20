-- test_case_results: per-test-case execution data, not just a final
-- verdict. submission_id is a plain TEXT identifier for now, no foreign
-- key -- there's no `submissions` table yet, since Phase 1.1 hasn't been
-- built. Add the FK once it exists.

CREATE TABLE IF NOT EXISTS test_case_results (
    id SERIAL PRIMARY KEY,
    submission_id TEXT NOT NULL,
    test_case_index INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    runtime_seconds REAL,
    timed_out BOOLEAN NOT NULL DEFAULT FALSE,
    compile_error BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_test_case_results_submission_id
    ON test_case_results (submission_id);
