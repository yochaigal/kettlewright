# Testing

## Running Tests

```bash
# Activate pipenv shell
pipenv shell
python -m pytest

# or run directly without shell activation
pipenv run python -m pytest
```

## Common Test Commands

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_basic.py

# Run with verbose output
python -m pytest -v

# Run tests in a specific class
python -m pytest tests/unit/test_template_filters.py::TestIntSumFilter
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
