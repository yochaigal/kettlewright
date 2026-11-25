"""Kettlewright's engine in a Flask app: init_app(app), the only part of the engine that knows Flask.

It serves the browser engine (static/kettlewright.js) and each system's own files, lets templates ask a
record for its system, and gives each page its system as data:

    /kettlewright/static/kettlewright.js   the browser engine, imported as '#kettlewright'
    /systems/<key>/static/...              a system's scripts and files (systems/<key>/static)
    templates                              a system's pieces (systems/<key>/templates/<key>/...), and the
                                           engine's generic ones (kettlewright/templates/kettlewright/...)

In templates:

    {{ kettlewright_importmap() }}         the import map: before any module script
    {{ kettlewright_manifest() }}          the page's system for kettlewright.js (the page's character's,
                                           party's or campaign's, else the default one)
    rules_for(record)                      a record's system; game_system is the default one
    {% include system_template('help/monster_format.html', party) %}
                                           the system's piece if it has one, else the engine's generic one

A system can plug in web parts of its own (like its ways of creating a character): its GameSystem names a
module (web = 'systems.<key>.web') whose init_app(app) is called here.
"""
import importlib
import json
from pathlib import Path

from flask import Blueprint, url_for
from jinja2 import pass_context
from markupsafe import Markup

from kettlewright.registry import SYSTEMS, load, system

SPECIFIER = '#kettlewright'
SCRIPT = 'kettlewright.js'
# The template variables a page's system is read from, in order.
PAGE_RECORDS = ('character', 'companion', 'party', 'campaign')


def rules_for(record=None):
    """A character's, companion's, party's or campaign's game system; the default one for anything else (a form,
    a generated preview, an undefined variable)."""
    return getattr(record, 'rules', None) or system()


def page_rules(context):
    """The system of the page's record (its character, companion, party or campaign), or the default one."""
    for name in PAGE_RECORDS:
        rules = getattr(context.get(name), 'rules', None)
        if rules is not None:
            return rules
    return system()


def script_url():
    try:
        return url_for('kettlewright.static', filename=SCRIPT)
    except RuntimeError:  # Outside a request (a test rewriting imports): the blueprint's fixed path.
        return f'/kettlewright/static/{SCRIPT}'


def imports():
    """The engine's entry for a page's import map (or for rewriting imports where no import map is allowed)."""
    return {SPECIFIER: script_url()}


def system_template(name, record=None):
    """Where a template piece is: the record's system's own (systems/<key>/templates/<key>/<name>), else the
    engine's generic one (kettlewright/templates/kettlewright/<name>). A list, for {% include %}."""
    return [f'{rules_for(record).key}/{name}', f'kettlewright/{name}']


def plugin(rules=None):
    """A system's web parts (the module its GameSystem names in web), or None: the default system's without rules."""
    rules = rules or system()
    return importlib.import_module(rules.web) if rules.web else None


def browser_manifest(rules, translate=lambda text: text):
    """The system for the browser engine, with its labels in the page's language."""
    data = rules.manifest()
    data['hp'] = dict(data['hp'], label=translate(rules.hit_points.abbr))
    data['attributes'] = [dict(attribute, label=translate(attribute['abbr'])) for attribute in data['attributes']]
    data['conditions'] = [dict(condition, label=translate(condition['label'])) for condition in data['conditions']]
    if rules.home and (Path(rules.home) / 'static' / 'rules.js').is_file():
        data['script'] = url_for(f'system_{rules.key}.static', filename='rules.js')
    return data


def init_app(app, translate=lambda text: text):
    """Plug the engine and the registered systems into the app. translate: the app's gettext, for labels."""
    load()
    app.register_blueprint(Blueprint('kettlewright', __name__, static_folder='static', template_folder='templates',
                                     static_url_path='/kettlewright/static'))
    for rules in list(SYSTEMS.values()):
        if rules.home:
            home = Path(rules.home)
            app.register_blueprint(Blueprint(
                f'system_{rules.key}', __name__, root_path=str(home),
                static_folder='static' if (home / 'static').is_dir() else None,
                static_url_path=f'/systems/{rules.key}/static',
                template_folder='templates' if (home / 'templates').is_dir() else None))
        if rules.web:
            importlib.import_module(rules.web).init_app(app)

    @pass_context
    def kettlewright_manifest(context, record=None):
        rules = rules_for(record) if record is not None else page_rules(context)
        data = json.dumps(browser_manifest(rules, translate)).replace('<', '\\u003c')
        return Markup(f'<script id="game-system" type="application/json">{data}</script>')

    def kettlewright_importmap(extra=None):
        mapping = json.dumps({'imports': {**(extra or {}), **imports()}})
        return Markup(f'<script type="importmap">{mapping}</script>')

    app.jinja_env.filters['translate_label'] = lambda label: translate(label)
    app.jinja_env.globals.update(
        rules_for=rules_for, system_template=system_template, kettlewright_manifest=kettlewright_manifest,
        kettlewright_importmap=kettlewright_importmap, kettlewright_imports=imports)

    @app.context_processor
    def default_system():
        return dict(game_system=system())
