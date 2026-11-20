"""Campaigns own their parties, character options and modules.

Every party now belongs to one campaign (parties.campaign_id). Existing parties
are filed like this, for the party's Warden:
1. the campaign the party was shown the most articles from (ties: oldest campaign);
2. otherwise a campaign it was linked to in the old campaign_parties table;
3. otherwise a new campaign named after the party.
Articles a party was shown from other campaigns stay visible to it.

Campaigns also keep custom backgrounds (NULL = none), whether the official
backgrounds are offered, and the modules added to them. The unused
campaign_parties table is dropped.
"""
from alembic import op
import sqlalchemy as sa

revision = '500a01'
down_revision = '430a01'
branch_labels = None
depends_on = None


def file_parties(connection):
    parties = connection.execute(sa.text(
        'SELECT id, owner, name FROM parties WHERE campaign_id IS NULL AND owner IS NOT NULL ORDER BY id')).all()
    for party_id, owner_id, name in parties:
        shown = connection.execute(sa.text(
            'SELECT c.id FROM party_presentations p '
            'JOIN content_entries e ON e.id = p.entry_id '
            'JOIN campaigns c ON c.id = e.campaign_id '
            'WHERE p.party_id = :party AND c.owner_id = :owner AND p.published '
            'GROUP BY c.id ORDER BY COUNT(p.id) DESC, c.id LIMIT 1'),
            {'party': party_id, 'owner': owner_id}).scalar()
        if shown is None:
            shown = connection.execute(sa.text(
                'SELECT c.id FROM campaign_parties l JOIN campaigns c ON c.id = l.campaign_id '
                'WHERE l.party_id = :party AND c.owner_id = :owner ORDER BY c.id LIMIT 1'),
                {'party': party_id, 'owner': owner_id}).scalar()
        if shown is None:
            connection.execute(sa.text(
                "INSERT INTO campaigns (owner_id, name, version, official_backgrounds, modules) "
                "VALUES (:owner, :name, 1, :official, '[]')"),
                {'owner': owner_id, 'name': (name or 'Party')[:200], 'official': True})
            shown = connection.execute(sa.text(
                'SELECT MAX(id) FROM campaigns WHERE owner_id = :owner'), {'owner': owner_id}).scalar()
        connection.execute(sa.text('UPDATE parties SET campaign_id = :campaign WHERE id = :party'),
                           {'campaign': shown, 'party': party_id})


def upgrade():
    with op.batch_alter_table('campaigns') as batch:
        batch.add_column(sa.Column('backgrounds', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('official_backgrounds', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column('modules', sa.JSON(), nullable=False, server_default='[]'))
    with op.batch_alter_table('parties') as batch:
        batch.add_column(sa.Column('campaign_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_parties_campaign_id', 'campaigns', ['campaign_id'], ['id'], ondelete='SET NULL')
        batch.create_index('ix_parties_campaign_id', ['campaign_id'])
    file_parties(op.get_bind())
    op.drop_table('campaign_parties')


def downgrade():
    op.create_table('campaign_parties',
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), primary_key=True),
    )
    op.execute('INSERT INTO campaign_parties (campaign_id, party_id) '
               'SELECT campaign_id, id FROM parties WHERE campaign_id IS NOT NULL')
    with op.batch_alter_table('parties') as batch:
        batch.drop_index('ix_parties_campaign_id')
        batch.drop_constraint('fk_parties_campaign_id', type_='foreignkey')
        batch.drop_column('campaign_id')
    with op.batch_alter_table('campaigns') as batch:
        batch.drop_column('modules')
        batch.drop_column('official_backgrounds')
        batch.drop_column('backgrounds')
