"""Stars (#476): bookmarks, listed first on the Campaigns page.

Anyone in a party stars it; a Warden stars their own modules, articles, maps and backgrounds.
A star is a row (user, kind, target, name). What it points at is checked again when listed, so
a star of something deleted, or no longer reachable, is simply not shown (and removed).
"""
from flask import abort, url_for
from flask_login import current_user
from slugify import slugify

from app.models import db, Campaign, ContentEntry, Module, Party, Star

KINDS = ('party', 'module', 'article', 'map', 'background')


def background_anchor(name):
    return 'background-' + (slugify(name) or 'unnamed')


def _target(kind, target_id, name, user_id):
    """What the star points at, if this person may still open it; else None."""
    from app.socket_events import party_recipient_ids
    if kind == 'party':
        party = db.session.get(Party, target_id)
        return party if party is not None and user_id in party_recipient_ids(party) else None
    if kind in ('module', 'background'):
        module = db.session.get(Module, target_id)
        if module is None or module.campaign is None or module.campaign.owner_id != user_id:
            return None
        if kind == 'background' and name not in (module.backgrounds or {}):
            return None
        return module
    if kind in ('article', 'map'):
        entry = db.session.get(ContentEntry, target_id)
        if entry is None or entry.owner_id != user_id or entry.category == 'party_note' or entry.campaign_id is None:
            return None
        return entry
    return None


def toggle_star(kind, target_id, name, on):
    """Star (on) or unstar something; 404 unless this person may open it."""
    if kind not in KINDS or (kind != 'background' and name):
        abort(400)
    if on and _target(kind, target_id, name, current_user.id) is None:
        abort(404)
    star = Star.query.filter_by(user_id=current_user.id, kind=kind, target_id=target_id, name=name).first()
    if on and star is None:
        db.session.add(Star(user_id=current_user.id, kind=kind, target_id=target_id, name=name))
    elif not on and star is not None:
        db.session.delete(star)
    db.session.commit()


def star_keys(user_id):
    """{(kind, target_id, name)}: to show a filled star."""
    return {(star.kind, star.target_id, star.name) for star in Star.query.filter_by(user_id=user_id)}


def starred_cards(user_id):
    """The cards of the Starred island: newest star first."""
    from app.lib.campaign_parties import party_page, member_portraits
    from app.lib.campaigns import map_only
    cards, stale = [], []
    for star in Star.query.filter_by(user_id=user_id).order_by(Star.created_at.desc(), Star.id.desc()):
        target = _target(star.kind, star.target_id, star.name, user_id)
        if target is None:
            stale.append(star)
            continue
        card = {'kind': star.kind, 'target_id': star.target_id, 'name': star.name, 'members': [], 'picture': None}
        if star.kind == 'party':
            card.update(title=target.name, url=party_page(target), subtitle=target.owner_username,
                        members=member_portraits(target),
                        picture=url_for('campaigns.party_image', party_id=target.id) if target.image else None)
        elif star.kind == 'module':
            card.update(title=target.title, subtitle=target.campaign.name,
                        url=url_for('campaigns.module_wiki', campaign_id=target.campaign_id, module_id=target.id))
        elif star.kind == 'background':
            card.update(title=star.name, subtitle=target.title,
                        url=url_for('campaigns.module_wiki', campaign_id=target.campaign_id, module_id=target.id)
                        + '#' + background_anchor(star.name))
        else:
            card.update(title=target.title or '?', subtitle=(target.module.title if target.module else target.campaign.name),
                        url=url_for('campaigns.wiki', campaign_id=target.campaign_id, entry_id=target.id),
                        picture=url_for('campaigns.entry_image', entry_id=target.id)
                        if target.image else None)
            card['kind'] = 'map' if map_only(target) else 'article'
        cards.append(card)
    if stale:  # Deleted, or out of reach: the star goes too.
        for star in stale:
            db.session.delete(star)
        db.session.commit()
    return cards
