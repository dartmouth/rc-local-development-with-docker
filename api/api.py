"""To-do API: stores to-dos in SQLite and serves them as JSON."""
import os
import socket
import sqlite3

from flask import Flask, jsonify, request

# Where the database file lives. Defaults to a file next to this script,
# but can be changed with the DB_PATH environment variable.
DB_PATH = os.environ.get("DB_PATH", "./data/todos.db")

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS todos ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " title TEXT NOT NULL,"
            " done INTEGER NOT NULL DEFAULT 0)"
        )


@app.get("/")
def hello():
    # Try editing this message while the app is running!
    return jsonify(
        message="Hello from the API!!",
        hostname=socket.gethostname(),
    )


@app.get("/todos")
def list_todos():
    with get_db() as conn:
        rows = conn.execute("SELECT id, title, done FROM todos ORDER BY id").fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/todos")
def add_todo():
    title = (request.get_json(silent=True) or {}).get("title", "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    with get_db() as conn:
        cur = conn.execute("INSERT INTO todos (title) VALUES (?)", (title,))
    return jsonify(id=cur.lastrowid, title=title, done=0), 201


@app.post("/todos/<int:todo_id>/toggle")
def toggle_todo(todo_id):
    with get_db() as conn:
        conn.execute("UPDATE todos SET done = 1 - done WHERE id = ?", (todo_id,))
    return "", 204


@app.delete("/todos/<int:todo_id>")
def delete_todo(todo_id):
    with get_db() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    return "", 204


init_db()

if __name__ == "__main__":
    app.run(port=5001)
