# Testing

## Running Tests

```bash
# Activate pipenv shell
pipenv shell
python -m pytest -p no:flask

# or run directly without shell activation
pipenv run python -m pytest -p no:flask
```

## Common Test Commands

```bash
# Run all tests
python -m pytest -p no:flask

# Run specific test file
python -m pytest -p no:flask tests/test_basic.py

# Run with verbose output
python -m pytest -p no:flask -v

# Run tests in a specific class
python -m pytest -p no:flask tests/unit/test_template_filters.py::TestIntSumFilter
```

## Writing Tests

Tests use pytest fixtures from `conftest.py`:

- `app` - Flask test app instance
- `client` - Test client for HTTP requests
- `app_context` - Application context for template/db access

Example:

```python
def test_something(app, client):
    with app.app_context():
        # Your test code here
        pass
```

The project supplies its own Flask fixtures. Disable the optional `pytest-flask`
plugin (`-p no:flask`) so HTTP requests from different users do not share an
application context or a cached login.
