"""Small helpers shared by the tests."""


def login(client, user_id, fresh=True):
    """Make `client` act as `user_id` (Flask-Login's session keys); fresh skips re-authentication prompts."""
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = fresh
    return client


def clients_for(app, user_ids):
    """One logged-in test client per user id, e.g. clients_for(app, [1, 2])[2].get(...)."""
    return {user_id: login(app.test_client(), user_id) for user_id in user_ids}
