"""Extract the same JSON table terms that the application translates at runtime."""
import json
from pathlib import Path
import runpy


# Importing app would initialize Flask and require a database during extraction.
TABLES = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'app/lib/translation_contexts.py'))
CONTEXTS = TABLES['_EVENTS_TRANSLATION_CONTEXTS']
IGNORED_KEYS = {'image', 'source', '_source', 'license', 'copyright'}


def extract_json(fileobj, keywords, comment_tags, options):
    filename = Path(fileobj.name)
    if filename.name in {'event_data.json', 'background_data.json', 'version.json'}:
        return

    def walk(node, path=()):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in IGNORED_KEYS:
                    continue
                # These dictionary keys, unlike schema fields, are visible names.
                if (filename.name in {'marketplace.json', 'traits.json'} and len(path) <= 1
                        or not path and filename.parent.name == 'backgrounds'
                        or path[-1:] == ('Group',)):
                    yield 1, '_', key, []
                yield from walk(value, path + (key,))
        elif isinstance(node, list):
            for item in node:
                yield from walk(item, path)
        elif (isinstance(node, str) and node and not node.isdecimal()
              and not node.startswith(('https://', 'http://'))
              and not node.endswith(('.webp', '.png', '.jpg'))):
            if filename.name == 'traits.json' and path:
                yield 1, '_', node, []
                yield 1, 'pgettext', ('character trait: ' + path[0], node), []
                return
            context = next((context for suffix, context in CONTEXTS.items()
                            if path[-len(suffix):] == suffix), None)
            if context:
                yield 1, '_', node, []
                yield 1, 'pgettext', (context, node), []
            else:
                yield 1, '_', node, []

    yield from walk(json.load(fileobj))
