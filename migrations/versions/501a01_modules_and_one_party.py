"""Modules inside campaigns; every campaign has a party; no unfiled articles.

A campaign now holds modules (articles, maps and backgrounds) and at least one party
(several for a West Marches game). Existing data is filed like this, for each Warden:
1. Unfiled articles (not party notes) go to a new campaign named "Unfiled articles".
2. A campaign without a party gets an empty one, named after the campaign.
3. Each campaign's articles and custom backgrounds become one module, named after the campaign.
campaigns.backgrounds and campaigns.modules move to the modules table.
"""
import json
import os
import re

from alembic import op
import sqlalchemy as sa

revision = '501a01'
down_revision = '500a01'
branch_labels = None
depends_on = None

CONTAINERS = '[{"name":"Main","slots":10,"id":0}]'


def loaded(value):
    """JSON columns read through raw SQL: text on SQLite, already parsed elsewhere."""
    if value is None or isinstance(value, (list, dict)):
        return value
    return json.loads(value)


def run(connection, sql, **params):
    statement = sa.text(sql)
    for name, value in params.items():
        if isinstance(value, (list, dict)):
            statement = statement.bindparams(sa.bindparam(name, type_=sa.JSON))
    return connection.execute(statement, params)


def new_campaign(connection, owner_id, name):
    run(connection, "INSERT INTO campaigns (owner_id, name, version, official_backgrounds, modules) "
                    "VALUES (:owner, :name, 1, :official, '[]')", owner=owner_id, name=name[:200], official=True)
    return run(connection, 'SELECT MAX(id) FROM campaigns WHERE owner_id = :owner', owner=owner_id).scalar()


def new_party(connection, campaign_id, owner_id, name):
    username = run(connection, 'SELECT username FROM users WHERE id = :id', id=owner_id).scalar()
    base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:150] or 'party'
    party_url, counter = base, 1
    while run(connection, 'SELECT 1 FROM parties WHERE owner = :owner AND party_url = :url',
              owner=owner_id, url=party_url).first():
        party_url, counter = f'{base}{counter}', counter + 1
    while True:
        code = os.urandom(8).hex()
        if not run(connection, 'SELECT 1 FROM parties WHERE join_code = :code', code=code).first():
            break
    run(connection, "INSERT INTO parties (owner, owner_username, name, description, members, subowners, join_code, "
                    "party_url, items, containers, version, campaign_id) VALUES (:owner, :username, :name, '', '[]', '[]', "
                    ":code, :url, '[]', :containers, 0, :campaign)",
        owner=owner_id, username=username, name=name[:64], code=code, url=party_url,
        containers=CONTAINERS, campaign=campaign_id)


def file_data(connection):
    # 1. Unfiled articles get a campaign of their own.
    owners = run(connection, "SELECT DISTINCT owner_id FROM content_entries "
                             "WHERE campaign_id IS NULL AND category != 'party_note' ORDER BY owner_id").scalars().all()
    for owner_id in owners:
        campaign_id = new_campaign(connection, owner_id, 'Unfiled articles')
        run(connection, "UPDATE content_entries SET campaign_id = :campaign "
                        "WHERE owner_id = :owner AND campaign_id IS NULL AND category != 'party_note'",
            campaign=campaign_id, owner=owner_id)
    # 2. Every campaign has a party.
    campaigns = run(connection, 'SELECT id, owner_id, name FROM campaigns ORDER BY id').all()
    for campaign_id, owner_id, name in campaigns:
        if not run(connection, 'SELECT 1 FROM parties WHERE campaign_id = :campaign', campaign=campaign_id).first():
            new_party(connection, campaign_id, owner_id, name)
    # 3. Each campaign's articles and backgrounds become one module.
    for campaign_id, name, backgrounds, recorded in run(
            connection, 'SELECT id, name, backgrounds, modules FROM campaigns ORDER BY id').all():
        backgrounds, recorded = loaded(backgrounds), loaded(recorded) or []
        has_entries = run(connection, 'SELECT 1 FROM content_entries WHERE campaign_id = :campaign',
                          campaign=campaign_id).first()
        if not has_entries and not backgrounds:
            continue
        # Named after the campaign. A module recorded under the campaign's own name (it was started
        # from it) keeps its slug; anything else recorded was added into the campaign and is merged here.
        started_from = next((item for item in recorded if item.get('title') == name), None)
        title, slug = name, (started_from or {}).get('slug') or ''
        run(connection, 'INSERT INTO modules (campaign_id, title, slug, backgrounds, version) '
                        'VALUES (:campaign, :title, :slug, :backgrounds, 1)',
            campaign=campaign_id, title=title[:200], slug=slug[:64], backgrounds=backgrounds or None)
        module_id = run(connection, 'SELECT MAX(id) FROM modules WHERE campaign_id = :campaign', campaign=campaign_id).scalar()
        run(connection, 'UPDATE content_entries SET module_id = :module WHERE campaign_id = :campaign',
            module=module_id, campaign=campaign_id)


def upgrade():
    op.create_table('modules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False, server_default=''),
        sa.Column('backgrounds', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False),
    )
    op.create_index('ix_modules_campaign_id', 'modules', ['campaign_id'])
    with op.batch_alter_table('content_entries') as batch:
        batch.add_column(sa.Column('module_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_content_entries_module_id', 'modules', ['module_id'], ['id'], ondelete='SET NULL')
        batch.create_index('ix_content_entries_module_id', ['module_id'])
    file_data(op.get_bind())
    with op.batch_alter_table('campaigns') as batch:
        batch.drop_column('modules')
        batch.drop_column('backgrounds')


def downgrade():
    with op.batch_alter_table('campaigns') as batch:
        batch.add_column(sa.Column('backgrounds', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('modules', sa.JSON(), nullable=False, server_default='[]'))
    connection = op.get_bind()
    for campaign_id, in run(connection, 'SELECT DISTINCT campaign_id FROM modules').all():
        backgrounds, recorded = {}, []
        for title, slug, found in run(connection, 'SELECT title, slug, backgrounds FROM modules '
                                                  'WHERE campaign_id = :campaign ORDER BY id', campaign=campaign_id).all():
            backgrounds.update(loaded(found) or {})
            recorded.append({'slug': slug, 'title': title})
        run(connection, 'UPDATE campaigns SET backgrounds = :backgrounds, modules = :recorded WHERE id = :campaign',
            backgrounds=backgrounds or None, recorded=recorded, campaign=campaign_id)
    # The campaigns and parties created by the upgrade stay: they hold the Warden's data.
    with op.batch_alter_table('content_entries') as batch:
        batch.drop_index('ix_content_entries_module_id')
        batch.drop_constraint('fk_content_entries_module_id', type_='foreignkey')
        batch.drop_column('module_id')
    op.drop_index('ix_modules_campaign_id', 'modules')
    op.drop_table('modules')
