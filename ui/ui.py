"""To-do UI: renders HTML pages and talks to the API on the server side."""
import os
import socket

import requests
from flask import Flask, redirect, render_template, request

# Where to find the API. Defaults to the API running on this same machine,
# but can be changed with the API_URL environment variable.
API_URL = os.environ.get("API_URL", "http://localhost:5001")

app = Flask(__name__)


def call_api(method, path, **kwargs):
    """Make a request to the API. Returns None if the API can't be reached."""
    try:
        return requests.request(method, f"{API_URL}{path}", timeout=3, **kwargs)
    except requests.RequestException:
        return None


@app.get("/")
def index():
    info = call_api("GET", "/")
    todos = call_api("GET", "/todos")
    reachable = info is not None and todos is not None
    return render_template(
        "index.html",
        api_info=info.json() if reachable else None,
        todos=todos.json() if reachable else [],
        api_url=API_URL,
        ui_hostname=socket.gethostname(),
    )


@app.post("/add")
def add():
    title = request.form.get("title", "").strip()
    if title:
        call_api("POST", "/todos", json={"title": title})
    return redirect("/")


@app.post("/toggle/<int:todo_id>")
def toggle(todo_id):
    call_api("POST", f"/todos/{todo_id}/toggle")
    return redirect("/")


@app.post("/delete/<int:todo_id>")
def delete(todo_id):
    call_api("DELETE", f"/todos/{todo_id}")
    return redirect("/")


if __name__ == "__main__":
    app.run(port=5002)
