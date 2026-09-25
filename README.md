# Docker for Local Development: To-do Demo

A tiny two-part app (a UI and an API, both in Python/Flask) used to show the
most common surprises of developing inside Docker, and how to fix each one.

```
 your browser ──> UI (port 5002) ──> API (port 5001) ──> SQLite file
```

The UI page shows which machine each part is running on and which address the
UI is using to reach the API. Keep an eye on that strip as you go.

## Two branches

- **`base`**: the app works when run directly on your computer. The Dockerfiles
  and `compose.yaml` are empty outlines for you to fill in.
- **`finished`**: everything filled in and fixed, with comments explaining each fix.

```bash
git checkout base       # start here
git checkout finished   # compare, or get unstuck
git diff base finished  # see every change at once
```

## What you need

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine with the compose plugin)
- Python 3.10+ (only for Step 0)

## Step 0: Run it on your computer, no Docker

```bash
uv init
uv sync

cd api && uv run api.py           # terminal 1
cd ui && uv run ui.py             # terminal 2
```

Open http://localhost:5002 and add a few to-dos. This is the goal: the same
experience, but with everything running in containers.

**Stop both apps (Ctrl+C) before moving on.** Otherwise Docker can't use ports
5001 and 5002 because they're already taken.

## The mental model

A container is a separate little computer running on your computer. It has its
own files, its own network, and its own `localhost`. Every problem below comes
from forgetting that.

## Challenges

Work on the `base` branch. Each challenge lists what you'll see, a hint, and
the explanation (click to expand). Run everything from the repo root with:

```bash
docker compose up --build
```

### 1. The container is running, but you can't reach it

Fill in `api/Dockerfile` and the `api` service in `compose.yaml`, then start it.
Visit http://localhost:5001.

**You'll see:** the connection fails, even though the logs say the app is running.

**Hint:** read the app's startup log line carefully. What address is it listening on?

<details>
<summary>Explanation</summary>

Flask listens on `127.0.0.1` (localhost) by default. Inside a container, that's
the *container's* localhost, which only the container itself can reach. Traffic
forwarded in from your computer arrives on a different network interface, so
nothing answers.

Fix: tell the app to listen on every interface with `host="0.0.0.0"`, and make
sure `compose.yaml` forwards the port with `ports: - "5001:5001"`.
</details>

### 2. You changed the code, but nothing changed

Edit the message in `api/app.py`, then refresh http://localhost:5001.

**You'll see:** the old message. Rebuilding with `docker compose up --build`
works, but it's slow, and you'd have to do it after every edit.

**Hint:** where does the container get its copy of the code?

<details>
<summary>Explanation</summary>

`COPY` puts a snapshot of your code into the image at build time. The container
can't see the files on your computer unless you share them.

Fix: a **bind mount** shares a folder from your computer with the container:

```yaml
volumes:
  - ./api:/app
```
</details>

### 3. The files are shared, but you still have to restart

With the bind mount in place, edit the message again and refresh.

**You'll see:** still the old message, until you restart the container.

**Hint:** the container sees the new file. Does the running Python process know it changed?

<details>
<summary>Explanation</summary>

Python loaded your code when it started and won't read it again on its own.
Restarting containers is slow and breaks your flow.

Fix: turn on Flask's auto-reloader with `debug=True`. It watches for file
changes and restarts the app inside the container in about a second. (Most
frameworks have an equivalent, such as `uvicorn --reload` or `nodemon`.)
</details>

### 4. The UI can't find the API

Fill in `ui/Dockerfile` and add a `ui` service to `compose.yaml`. Visit
http://localhost:5002.

**You'll see:** "Can't reach the API at http://localhost:5001", even though
that exact address works in your browser.

**Hint:** look at the strip at the top of the page. From *where* is the UI
trying to reach `localhost`?

<details>
<summary>Explanation</summary>

Your browser runs on your computer, where `localhost:5001` is forwarded to the
API. But the UI makes its API calls from inside its own container, where
`localhost` means the UI container itself. There's no API there.

Compose puts all services on a shared network where each one can be reached by
its **service name**. Fix it by pointing the UI at the API's service name:

```yaml
environment:
  API_URL: http://api:5001
```

(If the UI page doesn't load at all, you've met challenge 1 again.)
</details>

### 5. Your to-dos disappeared

Add some to-dos, then run `docker compose down` followed by `docker compose up`.

**You'll see:** an empty list.

**Hint:** where does the database file live, and what happens to it when the
container is removed?

<details>
<summary>Explanation</summary>

Anything a container writes (outside a mount) lives in that container's own
files, and `docker compose down` deletes the container. (`stop` and `restart`
keep it, which is why this can seem random.)

Fix: store the data in a **named volume**, which Docker keeps between runs:

```yaml
services:
  api:
    volumes:
      - api-data:/data

volumes:
  api-data:
```

To wipe the data on purpose, use `docker compose down -v`.
</details>

## The rules

1. Apps in containers must listen on `0.0.0.0`, not `localhost`.
2. The container only sees your files if you bind-mount them.
3. Use your framework's auto-reload so edits show up without restarting.
4. Containers reach each other by **service name**, not `localhost`.
5. Data you want to keep belongs in a **named volume**.

## Two more you'll meet eventually

- **Startup order.** If one service connects to another as soon as it starts
  (say, an API connecting to a database), it may start before the other is
  ready and crash. `depends_on` with a `healthcheck` in `compose.yaml` makes it wait.
- **Reaching your own computer from a container.** Inside a container,
  `localhost` is the container. To reach something running directly on your
  computer, use `host.docker.internal` (built into Docker Desktop; on Linux,
  add `extra_hosts: - "host.docker.internal:host-gateway"`).

## Dockerizing your own app

Copy the `finished` Dockerfile and compose file, then change:

1. The base image (`FROM`) to match your language.
2. The install command (`RUN`) and start command (`CMD`).
3. The port your app listens on, and make sure it's `0.0.0.0`.
4. The auto-reload option for your framework.
