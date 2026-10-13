"""SQLite persistence. All writes share an explicit transaction boundary."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from functools import wraps

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 password_hash TEXT NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0 CHECK(is_admin IN (0,1)));
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), csrf TEXT NOT NULL, expires_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS members(project_id INTEGER REFERENCES projects(id), user_id INTEGER REFERENCES users(id),
 role TEXT NOT NULL CHECK(role IN ('admin','analyst','reviewer','viewer')), PRIMARY KEY(project_id,user_id));
CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id), title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS requirements(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id), document_id INTEGER REFERENCES documents(id),
 uid TEXT NOT NULL, parent_id INTEGER REFERENCES requirements(id), title TEXT NOT NULL, statement TEXT NOT NULL, source TEXT NOT NULL DEFAULT '', rationale TEXT NOT NULL DEFAULT '',
 type TEXT NOT NULL CHECK(type IN ('functional','nonfunctional','constraint')), priority TEXT NOT NULL CHECK(priority IN ('must','should','could')),
 status TEXT NOT NULL CHECK(status IN ('draft','in_review','approved','archived')), owner_id INTEGER REFERENCES users(id), acceptance TEXT NOT NULL DEFAULT '',
 tags TEXT NOT NULL DEFAULT '[]', revision INTEGER NOT NULL DEFAULT 1, created_by INTEGER NOT NULL REFERENCES users(id), updated_at TEXT NOT NULL, UNIQUE(project_id,uid));
CREATE TABLE IF NOT EXISTS requirement_versions(id INTEGER PRIMARY KEY, requirement_id INTEGER NOT NULL REFERENCES requirements(id), revision INTEGER NOT NULL,
 snapshot TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL, UNIQUE(requirement_id,revision));
CREATE TABLE IF NOT EXISTS links(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id), source_id INTEGER NOT NULL REFERENCES requirements(id),
 target_id INTEGER NOT NULL REFERENCES requirements(id), kind TEXT NOT NULL CHECK(kind IN ('refines','depends','conflicts')), CHECK(source_id != target_id), UNIQUE(source_id,target_id,kind));
CREATE TABLE IF NOT EXISTS artifacts(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id), revision INTEGER NOT NULL DEFAULT 1, kind TEXT NOT NULL CHECK(kind IN ('design','test')),
 title TEXT NOT NULL, reference TEXT NOT NULL DEFAULT '', result TEXT NOT NULL DEFAULT 'not_run' CHECK(result IN ('not_run','passed','failed')));
CREATE TABLE IF NOT EXISTS artifact_links(requirement_id INTEGER REFERENCES requirements(id), artifact_id INTEGER REFERENCES artifacts(id), PRIMARY KEY(requirement_id,artifact_id));
CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, requirement_id INTEGER NOT NULL REFERENCES requirements(id), revision INTEGER NOT NULL,
 submitted_by INTEGER NOT NULL REFERENCES users(id), reviewer_id INTEGER NOT NULL REFERENCES users(id), status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
 comment TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, decided_at TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS one_pending_review ON reviews(requirement_id) WHERE status='pending';
CREATE TABLE IF NOT EXISTS changes(id INTEGER PRIMARY KEY, requirement_id INTEGER NOT NULL REFERENCES requirements(id), base_revision INTEGER NOT NULL,
 title TEXT NOT NULL, reason TEXT NOT NULL, proposed_json TEXT NOT NULL, submitted_by INTEGER NOT NULL REFERENCES users(id),
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')), decision_comment TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, decided_at TEXT);
CREATE TABLE IF NOT EXISTS baselines(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id), name TEXT NOT NULL, scope TEXT NOT NULL DEFAULT 'project' CHECK(scope IN ('project','selected')), created_by INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL, UNIQUE(project_id,name));
CREATE TABLE IF NOT EXISTS baseline_items(baseline_id INTEGER REFERENCES baselines(id), requirement_id INTEGER REFERENCES requirements(id), revision INTEGER NOT NULL,
 snapshot TEXT NOT NULL, PRIMARY KEY(baseline_id,requirement_id));
CREATE TABLE IF NOT EXISTS baseline_snapshots(baseline_id INTEGER PRIMARY KEY REFERENCES baselines(id), links_json TEXT NOT NULL, artifacts_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES projects(id), actor_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
 entity_type TEXT NOT NULL, entity_id INTEGER, detail TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS req_project ON requirements(project_id,status);
CREATE INDEX IF NOT EXISTS audit_project ON audit_logs(project_id,id);
CREATE INDEX IF NOT EXISTS links_target ON links(target_id);
"""

def connect(path):
    conn = sqlite3.connect(str(path), timeout=10, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA busy_timeout=10000')
    return conn

def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        # Additive migration preserves every historical payload in existing demos.
        for table, column, definition in [('artifacts','revision','INTEGER NOT NULL DEFAULT 1'), ('baselines','scope',"TEXT NOT NULL DEFAULT 'project'")]:
            if column not in {r['name'] for r in conn.execute(f'PRAGMA table_info({table})')}:
                conn.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
        for table in ('requirement_versions', 'baselines', 'baseline_items', 'baseline_snapshots', 'audit_logs'):
            for operation in ('UPDATE', 'DELETE'):
                conn.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'immutable historical record'); END")
    conn.close()

@contextmanager
def transaction(conn):
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise

def consistent_read(function):
    """Use one WAL snapshot for a composed read, reusing any caller transaction."""
    @wraps(function)
    def wrapped(conn, *args, **kwargs):
        if conn.in_transaction:
            return function(conn, *args, **kwargs)
        conn.execute('BEGIN')
        try:
            result = function(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
    return wrapped
