import os

import psycopg

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://devmentor:devmentor_dev_password@localhost:5432/devmentor",
).replace("postgresql+asyncpg://", "postgresql://")


def get_connection():
    return psycopg.connect(DB_URL)


def save_test_case_results(submission_id: str, judge_result: dict) -> None:
    """
    judge_result: the dict returned by runner.judge.judge_submission()
    (has "test_case_results", a list of per-case dicts).
    """
    rows = judge_result["test_case_results"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO test_case_results
                        (submission_id, test_case_index, verdict, stdout, stderr,
                         exit_code, runtime_seconds, timed_out, compile_error)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        submission_id,
                        row["test_case_index"],
                        row["verdict"],
                        row.get("stdout"),
                        row.get("stderr"),
                        row.get("exit_code"),
                        row.get("runtime_seconds"),
                        row.get("timed_out", False),
                        row.get("compile_error", False),
                    ),
                )
        conn.commit()


def get_test_case_results(submission_id: str) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT test_case_index, verdict, stdout, stderr, exit_code,
                       runtime_seconds, timed_out, compile_error
                FROM test_case_results
                WHERE submission_id = %s
                ORDER BY test_case_index
                """,
                (submission_id,),
            )
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
