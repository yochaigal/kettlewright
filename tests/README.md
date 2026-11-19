# Testing

## Running tests

```bash
# All Python tests (settings come from pytest.ini at the repository root)
pipenv run python -m pytest

# In parallel, one worker per CPU (pytest-xdist)
pipenv run python -m pytest -n auto

# One file, one test, or a class
python -m pytest tests/unit/test_campaigns.py
python -m pytest tests/unit/test_campaigns.py::test_map_reveal_shows_points_and_paths_progress
python -m pytest tests/unit/test_template_filters.py::TestIntSumFilter

# The slowest tests
python -m pytest --durations=20

# JavaScript tests (Node 22 or newer, no npm packages needed)
node --test 'tests/js/**/*.test.mjs'
```

Tests can be started from the repository root or from `tests/`; `conftest.py`
switches to the repository root because the app uses paths relative to it.

GitHub Actions runs both suites on every pull request (`.github/workflows/tests.yml`).

## Writing tests

Fixtures from `conftest.py`:

- `app` - the Flask app with an empty database. The app is built once per test
  session (per xdist worker); each test gets its rows deleted and its
  `app.config` and Babel setup restored afterwards, so changing them in a test is safe.
- `app_with_babel` - `app` with English translations set up.
- `client` - a test client for `app`.
- `app_context` - runs the test inside an application context.
- `fresh_app` - a brand-new app, for the rare test that must add request hooks or
  blueprints (Flask refuses those on an app that has already served requests).

Helpers from `tests/helpers.py`:

- `login(client, user_id)` - make a test client act as that user.
- `clients_for(app, [1, 2, 3])` - one logged-in client per user id.

```python
from tests.helpers import clients_for


def test_only_the_warden_can_rename(app_with_babel):
    with app_with_babel.app_context():
        ...  # add users, a party, characters
        db.session.commit()
    clients = clients_for(app_with_babel, [1, 2])
    assert clients[2].post('/party/edit/warden/party/save', data={...}).status_code == 403
```

Make requests outside `with app.app_context():` blocks. Requests made inside
one reuse that context, so Flask-Login's cached user leaks from one client to the next.

The optional `pytest-flask` plugin is disabled (`-p no:flask` in `pytest.ini`)
for the same reason: it keeps one application context for the whole test.
