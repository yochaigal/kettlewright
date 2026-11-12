"""Regenerate app/starter_adventures/ from the open Cairn first-party adventures.

Usage: python scripts/build_starter_adventures.py [--source DIR] [--only 1 2 ...]

Each CAS-N markdown file is split into a campaign.md plus one article per
top-level (# / ##) heading, in the front matter format that
app/lib/campaign_import.py reads. The text is CC-BY-SA 4.0 (see
THIRD-PARTY-NOTICES.md). Output is committed so deploys need no network.
"""
import argparse
import re
import shutil
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'app' / 'starter_adventures'
RAW = 'https://raw.githubusercontent.com/yochaigal/cairn/main/adventures/first-party/cas-{}.md'
SITE = 'https://cairnrpg.com'
MAX_BODY = 45000

TYPE_RULES = [
    (r'^(important )?npcs?\b|^npcs? stats', 'NPC'),
    (r'bestiary|monsters|creatures', 'Bestiary'),
    (r'^relics?\b', 'Relic'),
    (r'factions?$|^the order of|^the expedition team|^tideborn', 'Faction'),
    (r'^[a-z]?\d+[a-z]?\.\s', 'Location'),
    (r'introduction|setup|principles|really going on|warden|hooks|rumors|about this|'
     r'important information|on rules|overview|victim schedule|credits', 'Overview'),
]
# Headings the rules above cannot classify. Anything else inherits its parent's
# type when that is a place, NPC, bestiary or faction section, else becomes a Note.
OVERRIDES = {
    'twin lakes': 'Location', 'isthmus town': 'Location', 'farming path': 'Location',
    'dunston': 'Location', 'blue mouth caves': 'Location', 'rusal': 'Location',
    'tegny wood': 'Location', 'the mansion': 'Location', 'deadmill': 'Location',
    'the stone forest': 'Location', 'east lake pass': 'Location', 'the downs': 'Location',
    'white tower fens': 'Location', 'the white tower': 'Location', 'bone sump': 'Location',
    'temple of the fungal lizards': 'Location', 'vuk': 'NPC', 'vald lore': 'Lore',
    'the roots': 'Lore', 'olms': 'Bestiary', 'tube worms': 'Bestiary',
}


def github_slug(text):
    value = unicodedata.normalize('NFKC', text).lower()
    return re.sub(r'\s', '-', re.sub(r'[^\w\s-]', '', value, flags=re.UNICODE)).strip('-')


def file_slug(text):
    return re.sub(r'-+', '-', github_slug(text).replace('_', '-'))[:50].strip('-') or 'article'


def fetch(n, source):
    if source:
        return (Path(source) / f'cas-{n}.md').read_text(encoding='utf-8')
    with urllib.request.urlopen(RAW.format(n), timeout=30) as response:
        return response.read().decode('utf-8')


def split_front_matter(text):
    match = re.match(r'---\n(.*?)\n---\n', text, re.S)
    title = re.search(r'^title:\s*"?(.*?)"?\s*$', match.group(1), re.M).group(1).strip()
    return title, text[match.end():]


def clean(text):
    """Make source-site markdown self-contained for Kettlewright."""
    def nomarkdown(match):
        src = re.search(r'src="([^"]+)"', match.group(1))
        return f'![Map]({src.group(1)})' if src else ''
    text = re.sub(r'\{::nomarkdown\}\s*(.*?)\s*\{:/nomarkdown\}', nomarkdown, text, flags=re.S)
    text = re.sub(r'(!\[[^\]]*\]\()(/adventures/)', lambda m: m.group(1) + SITE + m.group(2), text)
    text = re.sub(r'(src=")(/adventures/)', lambda m: m.group(1) + SITE + m.group(2), text)
    text = re.sub(r'^- As markdown \(see below\)\s*\n', '', text, flags=re.M)
    return text.replace('\u00a0', ' ')


def headings(lines):
    fenced = False
    for i, line in enumerate(lines):
        if line.startswith('```'):
            fenced = not fenced
        match = None if fenced else re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', line)
        if match:
            yield i, len(match.group(1)), match.group(2).strip()


def kind_for(title, parent_kind):
    key = title.lower().strip()
    if key in OVERRIDES:
        return OVERRIDES[key]
    for pattern, kind in TYPE_RULES:
        if re.search(pattern, key):
            return kind
    return parent_kind if parent_kind in ('Location', 'NPC', 'Bestiary', 'Faction') else 'Note'


def sections(body, campaign_title):
    """Return (preamble, [section dicts]) split on # and ## headings."""
    lines = body.split('\n')
    marks = [(i, level, text) for i, level, text in headings(lines) if level <= 2]
    subtitle = campaign_title.split(':', 1)[-1].strip().lower()
    if marks and marks[0][1] == 1 and marks[0][2].lower() in (campaign_title.lower(), subtitle):
        lines[marks[0][0]] = ''
        marks = marks[1:]
    if not marks:
        raise SystemExit(f'{campaign_title}: no headings to split on')
    preamble = '\n'.join(lines[:marks[0][0]]).strip()
    found = []
    for n, (i, level, text) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(lines)
        found.append({'level': level, 'title': text, 'body': '\n'.join(lines[i + 1:end]).strip()})
    return preamble, found


def yaml_quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def write(path, title, kind, parent, body):
    lines = ['---', 'layout: default', f'title: {yaml_quote(title)}', f'type: {kind}']
    if parent:
        lines.append(f'parent: {yaml_quote(parent)}')
    lines += ['---', body.strip(), '']
    path.write_text('\n'.join(lines), encoding='utf-8')


def build(n, source):
    campaign_title, body = split_front_matter(fetch(n, source))
    body = clean(body)
    preamble, found = sections(body, campaign_title)

    parent_of, last_h1 = {}, None
    for index, item in enumerate(found):
        if item['level'] == 1:
            last_h1 = index
            parent_of[index] = None
        else:
            parent_of[index] = last_h1
    # Unique titles: the importer resolves `parent` by exact title across the archive.
    seen = {campaign_title}
    for index, item in enumerate(found):
        title = item['title']
        if title in seen:
            parent = parent_of[index]
            title = f"{title} ({found[parent]['title'] if parent is not None else campaign_title})"
        if title in seen:
            raise SystemExit(f'{campaign_title}: duplicate title {title!r}')
        seen.add(title)
        item['final'] = title

    anchors = {}
    for index, item in enumerate(found):
        anchors[github_slug(item['title'])] = index
        for _, _, text in headings(item['body'].split('\n')):
            anchors.setdefault(github_slug(text), index)

    def relink(text):
        def fix(match):
            label, slug = match.group(1), match.group(2)
            target = anchors.get(slug)
            if target is None:
                return label
            article = found[target]['final']
            return f'[[{article}|{label}]]' if label != article else f'[[{article}]]'
        return re.sub(r'\[([^\]]+)\]\(#([^)]+)\)', fix, text)

    out = OUT / f'cas-{n}'
    if out.exists():
        shutil.rmtree(out)
    (out / 'articles').mkdir(parents=True)

    notice = (f'*{campaign_title}* is a Cairn adventure by Yochai Gal and Cairn Press, '
              f'bundled with Kettlewright as a starter adventure under the '
              f'[CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) license. '
              f'Original: {SITE}/adventures/first-party/cas-{n}/')
    write(out / 'campaign.md', campaign_title, 'Campaign', None, relink(preamble) + '\n\n---\n\n' + notice)
    kinds = {}
    for index, item in enumerate(found):
        parent = parent_of[index]
        parent_kind = kinds.get(parent)
        kinds[index] = kind_for(item['title'], parent_kind)
        if len(item['body']) > MAX_BODY:
            raise SystemExit(f"{item['final']}: {len(item['body'])} chars, over {MAX_BODY}")
        parent_title = found[parent]['final'] if parent is not None else campaign_title
        write(out / 'articles' / f'{index + 1:02d}-{file_slug(item["title"])}.md',
              item['final'], kinds[index], parent_title, relink(item['body']))
    return campaign_title, [(item['final'], kinds[index], len(item['body'])) for index, item in enumerate(found)]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--source', help='directory holding cas-N.md instead of fetching')
    parser.add_argument('--only', nargs='+', type=int, default=[1, 2, 3, 4])
    args = parser.parse_args()
    for n in args.only:
        title, rows = build(n, args.source)
        print(f'{title}: {len(rows)} articles')
        for name, kind, size in rows:
            print(f'  {kind:9} {size:6}  {name}')


if __name__ == '__main__':
    main()
