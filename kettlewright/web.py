"""Kettlewright's engine in a Flask app: init_app(app), the only part of the engine that knows Flask.

It serves the browser engine (static/kettlewright.js) and the instance's system's own files, and gives each page
the system as data. The instance plays one system (GAME_SYSTEM, see registry.py):

    /kettlewright/static/kettlewright.js   the browser engine, imported as '#kettlewright'
    /system/<key>/static/...               the system's scripts and files (system/<key>/static)
    templates                              the system's pieces (system/<key>/templates/<key>/...), and the
                                           engine's generic ones (kettlewright/templates/kettlewright/...)

In templates:

    {{ kettlewright_importmap() }}         the import map: before any module script
    {{ kettlewright_manifest() }}          the system, for kettlewright.js
    game_system                            the system: its stats, conditions and rules
    {% include system_template('help/monster_format.html') %}
                                           the system's piece if it has one, else the engine's generic one

A system can plug in web parts of its own (like its ways of creating a character): its GameSystem names a
module (web = 'system.<key>.web') whose init_app(app) is called here.
"""
import importlib
import json
from pathlib import Path

from flask import Blueprint, url_for
from markupsafe import Markup

from kettlewright.registry import load, system

SPECIFIER = '#kettlewright'
SCRIPT = 'kettlewright.js'


def script_url():
    try:
        return url_for('kettlewright.static', filename=SCRIPT)
    except RuntimeError:  # Outside a request (a test rewriting imports): the blueprint's fixed path.
        return f'/kettlewright/static/{SCRIPT}'


def imports():
    """The engine's entry for a page's import map (or for rewriting imports where no import map is allowed)."""
    return {SPECIFIER: script_url()}


def system_template(name):
    """Where a template piece is: the system's own (system/<key>/templates/<key>/<name>), else the engine's generic
    one (kettlewright/templates/kettlewright/<name>). A list, for {% include %}."""
    return [f'{system().key}/{name}', f'kettlewright/{name}']


def plugin():
    """The system's web parts (the module its GameSystem names in web), or None."""
    rules = system()
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
    """Plug the engine and the instance's system into the app. translate: the app's gettext, for labels."""
    rules = load()
    app.register_blueprint(Blueprint('kettlewright', __name__, static_folder='static', template_folder='templates',
                                     static_url_path='/kettlewright/static'))
    if rules.home:
        home = Path(rules.home)
        app.register_blueprint(Blueprint(
            f'system_{rules.key}', __name__, root_path=str(home),
            static_folder='static' if (home / 'static').is_dir() else None,
            static_url_path=f'/system/{rules.key}/static',
            template_folder='templates' if (home / 'templates').is_dir() else None))
    if rules.web:
        importlib.import_module(rules.web).init_app(app)

    def kettlewright_manifest():
        data = json.dumps(browser_manifest(system(), translate)).replace('<', '\\u003c')
        return Markup(f'<script id="game-system" type="application/json">{data}</script>')

    def kettlewright_importmap(extra=None):
        mapping = json.dumps({'imports': {**(extra or {}), **imports()}})
        return Markup(f'<script type="importmap">{mapping}</script>')

    app.jinja_env.filters['translate_label'] = lambda label: translate(label)
    app.jinja_env.globals.update(
        system_template=system_template, kettlewright_manifest=kettlewright_manifest,
        kettlewright_importmap=kettlewright_importmap, kettlewright_imports=imports)

    @app.context_processor
    def the_game_system():
        return dict(game_system=system())
