# tests/conftest.py
import os
import sqlite3
import pytest

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users(
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS exams(
  exam_id TEXT PRIMARY KEY, exam_type TEXT, date TEXT, year INTEGER
);
CREATE TABLE IF NOT EXISTS questions(
  exercise_id TEXT PRIMARY KEY, exam_id TEXT,
  question TEXT, solution TEXT, topic_pred TEXT
);
CREATE TABLE IF NOT EXISTS attempts(
  attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL, user_id INTEGER, exercise_id TEXT,
  score REAL, correct INTEGER, reasons TEXT, hint TEXT
);
"""

@pytest.fixture(scope="session")
def tmp_db(tmp_path_factory):
    db = tmp_path_factory.mktemp("data") / "exams.db"
    os.environ["DB_PATH"] = str(db)       # app reads this
    os.environ["USE_LLM"] = "false"       # keep tests fast/deterministic

    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.executescript(SCHEMA_SQL)

    # --- seed minimal rows while DB is OPEN ---
    cur.execute("""
    INSERT OR REPLACE INTO exams (exam_id, exam_type, date, year)
    VALUES ('General_2025-08-29','General','2025-08-29',2025)
    """)
    cur.execute("""
    INSERT OR REPLACE INTO questions (exercise_id, exam_id, question, solution, topic_pred)
    VALUES ('General_2025-08-29_Exercise_1','General_2025-08-29',
            'State the Riesz representation theorem.',
            'Every bounded linear functional on a Hilbert space equals <·,y> for a unique y.',
            'linear functional')
    """)
    con.commit()
    con.close()

    return str(db)

# optional: force LLM to no-op if your app still tries to call it
@pytest.fixture(autouse=True)
def disable_llm(monkeypatch):
    try:
        import mqth_q.grading as grading
        monkeypatch.setattr(grading, "llm_grade_and_feedback", lambda *a, **k: None, raising=False)
    except Exception:
        try:
            import grading
            monkeypatch.setattr(grading, "llm_grade_and_feedback", lambda *a, **k: None, raising=False)
        except Exception:
            pass

@pytest.fixture()
def client(tmp_db):
    from fastapi.testclient import TestClient
    import importlib, app   # adjust if your app module has another name
    importlib.reload(app)   # import AFTER env is set
    return TestClient(app.app)
