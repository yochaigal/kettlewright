# Dev Container for Kettlewright

This dev container provides a complete development environment for Kettlewright.

## Ways to Use This Dev Container

### 1. VS Code (Local) ⭐ Recommended

**This is the only tested method and is recommended for contributors. If you want support or bug fixes for local dev, use this.**

**Prerequisites:**
- [Docker](https://www.docker.com/products/docker-desktop)
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

**Steps:**
1. Open the project in VS Code
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Wait for the container to build and start (post-create script will set up the database automatically)
4. Run the Flask development server:
   - **Option A (Recommended):** Press `F5` to start debugging with auto-reload
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

# Or with gunicorn (production-like)
gunicorn -k eventlet -w 1 -b 0.0.0.0:8000 app:application
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

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

## Environment Variables

The dev container sets these by default:
- `FLASK_APP=app:application`
- `FLASK_ENV=development`
- `DATABASE_URL=sqlite:///instance/kettlewright.db`
- `SECRET_KEY=dev-secret-key-change-in-production`
- `USE_REDIS=false`

To customize, create a `.env` file in the project root.

## Using Redis (Optional)

To enable Redis for development:

1. Uncomment the Redis service in `.devcontainer/docker-compose.yml`
2. Rebuild the container
3. Set `USE_REDIS=true` in your environment

## Tips

- The workspace is mounted at `/workspace`
- Changes to files are reflected immediately
- Python packages are installed in the container
- Database persists in the `instance/` directory on your host
