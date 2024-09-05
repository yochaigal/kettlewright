import logging
from logging.config import fileConfig
from flask import current_app
from alembic import context

# Alembic Config object for accessing .ini file values
config = context.config

# Configure Python logging
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # For Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except TypeError:
        # For Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    engine = get_engine()
    if hasattr(engine, 'url') and hasattr(engine.url, 'render_as_string'):
        return engine.url.render_as_string(hide_password=False).replace('%', '%%')
    return str(engine.url).replace('%', '%%')


# Set the SQLAlchemy URL for migrations
config.set_main_option('sqlalchemy.url', get_engine_url())

# Target database metadata object for autogenerate support
target_db = current_app.extensions['migrate'].db


def get_metadata():
    # Return the appropriate metadata object
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True,
        render_as_batch=True,  # Ensure batch mode is enabled for offline migrations
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.warning('No changes in schema detected.')

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            process_revision_directives=process_revision_directives,
            # Remove explicit render_as_batch, rely on configure_args instead
            **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

