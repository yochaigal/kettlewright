"""Human-readable wiki links with stable, audience-specific article bindings."""
from html import escape
import posixpath
import re
import unicodedata
from uuid import uuid4
from urllib.parse import unquote

import mistune
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models import db, ContentEntry, PartyPresentation


def destination(value):
    return unquote(value).strip()


def internal_destination(value):
    return bool(value) and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:|^//|^/', value)


def heading_id(text):
    value = unicodedata.normalize('NFKC', text).lower()
    value = re.sub(r'[^\w\s-]', '', value, flags=re.UNICODE)
    return 'kw-h-' + re.sub(r'[\s_]+', '-', value).strip('-')


def wiki_plugin(md):
    def parse(inline, match, state):
        raw = match.group(0)[2:-2]
        target, _, label = raw.partition('|')
        state.append_token({'type': 'wiki_link', 'attrs': {'target': destination(target),
                            'label': label.strip() or target.strip()}})
        return match.end()
    md.inline.register('wiki_link', r'(?<!!)\[\[[^\]\n]+\]\]', parse, before='link')


ast = mistune.create_markdown(renderer='ast', plugins=['strikethrough', 'table', wiki_plugin])


def tokens(body):
    if not body or body.startswith('<!--kw-rich-text:1-->'):
        return []
    result = []
    def walk(items):
        for item in items:
            if item['type'] == 'wiki_link':
                result.append(item['attrs']['target'])
            elif item['type'] == 'link':
                target = destination(item['attrs']['url'])
                if internal_destination(target):
                    result.append(target)
            walk(item.get('children', []))
    walk(ast(body))
    return list(dict.fromkeys(result))


def headings(body):
    result, counts, parents = [], {}, []
    def plain(items):
        return ''.join(item.get('raw', item.get('attrs', {}).get('label', '')) + plain(item.get('children', [])) for item in items)
    for item in ast(body or ''):
        if item['type'] == 'heading':
            text = plain(item.get('children', []))
            level = item['attrs']['level']
            while parents and parents[-1][0] >= level:
                parents.pop()
            parents.append((level, text))
            slug = heading_id(text)
            counts[slug] = counts.get(slug, 0) + 1
            result.append({'title': text, 'path': '#'.join(parent[1] for parent in parents),
                           'anchor': slug + (f'-{counts[slug]}' if counts[slug] > 1 else '')})
    return result


def resolve_token(token, source, candidates):
    path = token.partition('#')[0]
    if not path:
        return source
    normalized = posixpath.normpath(path).removesuffix('.md')
    relative = posixpath.normpath(posixpath.join(posixpath.dirname(source.source_path or ''), path)).removesuffix('.md')
    if '/' not in path and not path.endswith('.md'):
        titled = [entry for entry in candidates if entry.title == path]
        if titled:
            return titled[0] if len(titled) == 1 else None
    exact = [entry for entry in candidates if entry.source_path and
             entry.source_path.removesuffix('.md') in (normalized, relative)]
    if exact:
        return exact[0] if len(exact) == 1 else None
    matches = [entry for entry in candidates if entry.title == normalized or
        entry.source_path and posixpath.basename(entry.source_path).removesuffix('.md') == normalized]
    return matches[0] if len(matches) == 1 else None


def bind_references(source, body, previous=None, candidates=None):
    if candidates is None:
        campaign_id = source.campaign.id if source.campaign is not None else source.campaign_id
        candidates = ContentEntry.query.filter_by(owner_id=source.owner_id, campaign_id=campaign_id).all()
        candidates += [entry for entry in db.session.new if isinstance(entry, ContentEntry)
            and entry.owner_id == source.owner_id and
            (entry.campaign.id if entry.campaign is not None else entry.campaign_id) == campaign_id]
    owned = {entry.reference_key: entry for entry in candidates if entry.owner_id == source.owner_id}
    result = {}
    for token in tokens(body):
        old = (previous or {}).get(token)
        target = owned.get(old) if isinstance(old, str) else None
        if target is None:
            target = resolve_token(token, source, candidates)
        if target is not None and target.reference_key:
            result[token] = target.reference_key
    return result


@event.listens_for(Session, 'before_flush')
def bind_saved_articles(session, *_):
    # All editing paths (article forms, map cards and generated children) use
    # the same binding rule. Publication bindings are stored independently.
    changed = list(session.new | session.dirty)
    for row in session.new:
        if isinstance(row, ContentEntry) and not row.reference_key:
            row.reference_key = uuid4().hex
    for row in changed:
        if isinstance(row, ContentEntry):
            state = inspect(row)
            if not row.source_path and row.title:
                name = re.sub(r'[\\/:\x00-\x1f]', '-', row.title).strip().strip('.') or 'article'
                path = f'articles/{name[:180]}.md'
                campaign_id = row.campaign.id if row.campaign is not None else row.campaign_id
                existing = session.query(ContentEntry).filter_by(owner_id=row.owner_id,
                    campaign_id=campaign_id, source_path=path).first()
                if existing or any(other is not row and isinstance(other, ContentEntry)
                    and other.owner_id == row.owner_id and other.source_path == path for other in session.new):
                    path = f'articles/{name[:180]}-{uuid4().hex[:8]}.md'
                row.source_path = path
            if row in session.new or state.attrs.body.history.has_changes():
                if not state.attrs.references.history.has_changes():
                    with session.no_autoflush:
                        row.references = bind_references(row, row.body or '', row.references)
        elif isinstance(row, PartyPresentation):
            state = inspect(row)
            if row in session.new or state.attrs.body.history.has_changes():
                if not state.attrs.references.history.has_changes():
                    source = row.entry or session.get(ContentEntry, row.entry_id)
                    if source is not None:
                        previous = dict(source.references or {})
                        previous.update(row.references or {})
                        with session.no_autoflush:
                            row.references = bind_references(source, row.body or '', previous)


def reference_urls(body, bindings, entries, party_id=None):
    result = {}
    by_key = {(entry.get('reference_key') if isinstance(entry, dict) else entry.reference_key): (entry_id, entry)
              for entry_id, entry in entries.items()}
    for token in tokens(body):
        resolved = by_key.get((bindings or {}).get(token))
        if resolved is None:
            continue
        target_id, target = resolved
        target_body = target['body'] if isinstance(target, dict) else target.body
        fragment = token.partition('#')[2]
        anchor = ''
        if fragment:
            if fragment.startswith('^'):
                continue  # Block references are a later feature.
            available = headings(target_body)
            requested = heading_id(fragment)
            match = next((heading for heading in available if heading['path'].casefold() == fragment.casefold()), None)
            if match is None:
                match = next((heading for heading in available if heading['anchor'] == requested or heading['title'] == fragment), None)
            if match is None:
                continue
            anchor = '#' + match['anchor']
        result[token] = (f'/party/{party_id}/materials/{target_id}' if party_id is not None
                         else f'/materials/{target_id}/edit') + anchor
    return result


def private_reference_urls(entry):
    candidates = ContentEntry.query.filter_by(owner_id=entry.owner_id, campaign_id=entry.campaign_id).all()
    bindings = bind_references(entry, entry.body, entry.references, candidates)
    return reference_urls(entry.body, bindings, {item.id: item for item in candidates})


def prepare_archive_references(payload):
    from types import SimpleNamespace
    rows = payload['rows']
    articles = [SimpleNamespace(id=i, owner_id=0, campaign_id=None, campaign=None,
        reference_key=str(i),
        title=row['title'], body=row['body'], source_path=row.get('source_path') or row['file'])
        for i, row in enumerate(rows) if row['category'] != 'campaign']
    def root(i):
        while rows[i]['parent'] is not None:
            i = rows[i]['parent']
        return i if rows[i]['category'] == 'campaign' else None
    by_id = {article.id: article for article in articles}
    explicit = {}
    for link in payload.get('reference_bindings', []):
        explicit.setdefault(link['source'], {})[link['token']] = str(link['target'])
    for article in articles:
        candidates = [target for target in articles if root(target.id) == root(article.id)]
        bound = bind_references(article, article.body, explicit.get(article.id), candidates)
        rows[article.id]['references'] = {token: int(target) for token, target in bound.items()}
        urls = reference_urls(article.body, bound, by_id)
        for token in tokens(article.body):
            if token not in urls:
                payload['warnings'].append(f'{rows[article.id]["file"]}: unresolved article link "{token}"; it will remain plain text.')


class ReferenceRenderer(mistune.HTMLRenderer):
    def __init__(self, references):
        super().__init__(escape=False)
        self.references, self.heading_counts = references or {}, {}

    def wiki_link(self, target, label):
        url = self.references.get(target)
        return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>' if url else escape(label)

    def link(self, text, url, title=None):
        key = destination(url)
        if internal_destination(key):
            resolved = self.references.get(key)
            return f'<a href="{escape(resolved, quote=True)}">{text}</a>' if resolved else text
        return super().link(text, url, title)

    def heading(self, text, level, **attrs):
        plain = re.sub('<[^>]*>', '', text)
        from html import unescape
        slug = heading_id(unescape(plain))
        self.heading_counts[slug] = self.heading_counts.get(slug, 0) + 1
        anchor = slug + (f'-{self.heading_counts[slug]}' if self.heading_counts[slug] > 1 else '')
        return f'<h{level} id="{escape(anchor, quote=True)}">{text}</h{level}>\n'
