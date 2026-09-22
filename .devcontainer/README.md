# Dev Container for Kettlewright

This dev container provides a complete development environment for Kettlewright.

## Ways to Use This Dev Container

### Docker Compose (any editor)

Prepare the root `.env` as described under **Environment Variables** below.
From the repository root, run:

```bash
docker compose -f .devcontainer/docker-compose.yml up -d --build
docker compose -f .devcontainer/docker-compose.yml logs -f --tail=100 app
```

The first build downloads Python and installs application and test dependencies.
The shared `post-create.sh` setup runs before Flask starts, compiling translations
and applying database migrations. Open http://127.0.0.1:8000 when the server is ready.
Register an account, then open http://127.0.0.1:8025 to find the confirmation
email in Mailpit. Messages stay local; no external SMTP account is needed.

The repository is mounted in `/workspace`. Python edits automatically restart
Flask; refresh the browser after editing templates, JavaScript, CSS or SCSS.
SCSS is compiled automatically. Browser refresh is manual.
Rebuild only after changing dependencies or the Dockerfile.

If `requirements.txt` changes (for example, to add Pillow for portrait uploads),
run `docker compose -f .devcontainer/docker-compose.yml up -d --build app`.
A restart applies migrations but does not install new dependencies. Packages
installed manually with `pip` inside a running container are lost when that
container is recreated from the old image. Uploaded portraits persist in
`instance/portraits` on the host, alongside the SQLite database.

```bash
# Stop containers (the SQLite database stays in instance/)
docker compose -f .devcontainer/docker-compose.yml down

# Start again without rebuilding
docker compose -f .devcontainer/docker-compose.yml up -d

# Apply new migrations by restarting the app
docker compose -f .devcontainer/docker-compose.yml restart app

# Apply changes to .env
docker compose -f .devcontainer/docker-compose.yml up -d --force-recreate app
```

Do not start a second Flask server via F5 when using this mode. For IDE-managed
Dev Containers, `overrideCommand` keeps the app container idle so you can start
the server with the debugger instead. Stop the Compose session before switching
to IDE-managed Dev Containers to free ports 8000 and 8025.

### 1. VS Code (Local) ⭐ Recommended

**This is the only tested method and is recommended for contributors. If you want support or bug fixes for local dev, use this.**

**Prerequisites:**
- [Docker](https://www.docker.com/products/docker-desktop)
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

**Steps:**
1. Prepare the root `.env` (see below), then open the project in VS Code
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Wait for the container to build and start (post-create script will set up the database automatically)
4. Run the Flask development server:
   - **Option A (Recommended):** Select **Flask: Run with Auto-reload**, then press `F5`
   - **Option B:** Run in terminal: `flask run --host=0.0.0.0 --port=8000`
5. The application will be available at `http://localhost:8000`

### 2. GitHub Codespaces (Cloud)

**No local installation required!**

1. Go to the repository on GitHub
2. Click the green **Code** button
3. Select the **Codespaces** tab
4. Click **Create codespace on [branch]**
5. Wait for the environment to build (2-3 minutes)
6. The app will be available at the forwarded port

**Benefits:**
- ✅ No local Docker or VS Code needed
- ✅ Works in your browser
- ✅ Free tier available (60 hours/month)
- ✅ Powerful cloud machines

### 3. devcontainer CLI

**Prerequisites:**
- [Docker](https://www.docker.com/products/docker-desktop)
- [Dev Container CLI](https://github.com/devcontainers/cli)

**Steps:**
```bash
# Install the CLI
npm install -g @devcontainers/cli

# Build and run the dev container
devcontainer up --workspace-folder .

# Execute commands in the container
devcontainer exec --workspace-folder . flask run
```

### 4. JetBrains IDEs (IntelliJ, PyCharm, etc.)

**Prerequisites:**
- JetBrains IDE with Docker plugin
- [Dev Containers support](https://www.jetbrains.com/help/idea/connect-to-devcontainer.html)

**Steps:**
1. Open the project
2. IDE should detect `.devcontainer/devcontainer.json`
3. Click the notification to use the dev container
4. Wait for build and sync

### 5. Bring Your Own Tooling

Roll on the **Development Environment Setup** table (d6):
1. Neovim in tmux, obviously
2. Emacs with TRAMP mode because you're cursed
3. Docker + your favorite text editor from 1995
4. SSH into the container and vi like it's 1976
5. Carrier pigeon with punch cards
6. You're already in production, aren't you?

## What's Included

- Python 3.11
- All dependencies from `requirements.txt`
- SQLite database (in `instance/` directory)
- Git and GitHub CLI
- VS Code extensions for Python, Docker, and web development
- Auto-configured Python testing with pytest
- Shared debug configurations in `.vscode/launch.json` for consistent development experience

## Running the Application

### Using VS Code Debugger (Recommended)

The project includes pre-configured debug settings in `.vscode/launch.json` that are shared with all contributors.

Press **F5** or go to **Run and Debug** (Ctrl+Shift+D) and select one of these configurations:

- **Flask: Run with Auto-reload** - Development mode with hot-reload (recommended for coding)
- **Flask: Run App** - Debug mode without auto-reload (better for breakpoint debugging)
- **Python: Run Tests** - Run all pytest tests
- **Python: Debug Current Test** - Debug the currently open test file

### Using Terminal

```bash
# With Flask development server (with auto-reload)
flask run --host=0.0.0.0 --port=8000

# Or with gunicorn (production-like, stop Flask first)
USE_FLASK=False FLASK_DEBUG=0 gunicorn -k eventlet -w 1 -b 0.0.0.0:8000 app:application
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/bonds/test_json_export_and_printing.py

# Run with coverage
pytest --cov=app
```

### Initialization and post-create.sh

Run `.devcontainer/post-create.sh` **inside the container**, not on the host.
Both startup modes use the same script:

- **Docker Compose:** the app command runs it on every container start, before
  Flask. A setup failure prevents the server from starting.
- **IDE-managed Dev Containers / devcontainer CLI:** `postCreateCommand` runs it
  when the container is created or rebuilt, before you start Flask manually.
  Simply reopening an existing container does not rerun it.

The script creates `instance/`, compiles translation catalogs, and runs
`flask db upgrade`. Loading the Flask app also compiles the static assets.
It applies only pending migrations and preserves existing data; no separate
`flask db init` or manual database creation is needed.
Dependencies are installed in `Dockerfile.dev`, so setup does not reinstall them.

To rerun setup with plain Docker Compose, restart the app:

```bash
docker compose -f .devcontainer/docker-compose.yml restart app
docker compose -f .devcontainer/docker-compose.yml logs -f --tail=100 app
```

In an IDE-managed container, stop Flask and run this from `/workspace`, then
start Flask again:

```bash
bash .devcontainer/post-create.sh
```

### Database Migrations

After pulling changes containing new migrations, restart the app in Compose
mode, or rerun the setup script in an IDE-managed container as described above.
Python auto-reload does not apply database migrations.

From the repository root on the host, inspect migration status with:

```bash
docker compose -f .devcontainer/docker-compose.yml exec app flask db current
docker compose -f .devcontainer/docker-compose.yml exec app flask db heads
```

If the app has exited because a migration failed, inspect its logs and fix the
reported problem. You can then retry migrations in a one-off container:

```bash
docker compose -f .devcontainer/docker-compose.yml stop app
docker compose -f .devcontainer/docker-compose.yml run --rm --no-deps app flask db upgrade
docker compose -f .devcontainer/docker-compose.yml up -d app
```

Only create a new migration when you intentionally change database models:

```bash
docker compose -f .devcontainer/docker-compose.yml exec app flask db migrate -m "Description of changes"
```

Review the generated file under `migrations/versions/`, then restart the app to
apply it. Commit the migration alongside the model changes.

Inside an IDE-managed container, use the same Flask commands directly:

```bash
flask db current
flask db heads
flask db upgrade
```

## Environment Variables

Compose reads `.env` from the repository root. This file is ignored by Git.
For a fresh checkout, create it with these local settings (replace the secret
with a random value, for example from `openssl rand -hex 32`):

```dotenv
BASE_URL=http://127.0.0.1:8000
SECRET_KEY=replace-with-a-random-secret
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite
MAIL_SERVER=mailpit
MAIL_PORT=1025
MAIL_USE_TLS=
MAIL_USERNAME=kettlewright@local.test
MAIL_PASSWORD=local-only
USE_CAPTCHA=False
CAPTCHA_BLOCK=False
```

Keep `MAIL_USE_TLS` empty: the app currently reads it as a string, so `False`
would also enable TLS. Mailpit accepts the local SMTP credentials above.
Its messages are temporary and may disappear when the container is recreated.

Compose enables `FLASK_DEBUG=1`, `USE_FLASK=True`, `USE_REDIS=False` and
`REQUIRE_SIGNUP_CODE=False`. The SQLite database persists in `instance/db.sqlite`.
Keep `.env` with database backups to preserve the secret key.

## Using Redis (Optional)

To enable Redis for development:

1. Uncomment the Redis service in `.devcontainer/docker-compose.yml`
2. Rebuild the container
3. Set `USE_REDIS=True` in the Compose environment and add
   `REDIS_URL=redis://redis:6379/0` to `.env`

## Tips

- The workspace is mounted at `/workspace`
- Changes to files are reflected immediately
- Python packages are installed in the container
- Database persists in the `instance/` directory on your host
