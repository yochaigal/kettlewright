"""HTTP interactions and OAuth account linking for the optional Discord app."""
import hmac
import json
import secrets
import time
from urllib.parse import urlencode

import click
import requests
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_babel import _
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError

from app.lib.character_rolls import publish_roll
from app.lib.discord_commands import autocomplete, command_definition, execute, reply, site_url
from app.lib.socket_rate_limit import SocketRateLimiter
from app.models import DiscordAccount, DiscordChannel, DiscordInteraction, DiscordSelection, db

discord = Blueprint('discord', __name__)
API = 'https://discord.com/api/v10'


def snowflake(value):
    return isinstance(value, str) and value.isascii() and value.isdecimal() and 1 <= len(value) <= 20


def enabled():
    return all(current_app.config.get('DISCORD_' + key) for key in
               ('APPLICATION_ID', 'PUBLIC_KEY', 'CLIENT_SECRET', 'BASE_URL'))


@discord.route('/account/discord', methods=['GET', 'POST'])
@login_required
def settings():
    form = FlaskForm()
    account = db.session.get(DiscordAccount, current_user.id)
    if request.method == 'POST':
        if not form.validate_on_submit():
            abort(400)
        if request.form.get('action') == 'disconnect':
            DiscordSelection.query.filter_by(user_id=current_user.id).delete()
            bindings = DiscordChannel.query.filter_by(linked_by=current_user.id).all()
            for binding in bindings:
                DiscordSelection.query.filter_by(guild_id=binding.guild_id, channel_id=binding.channel_id).delete()
                db.session.delete(binding)
            if account:
                db.session.delete(account)
            db.session.commit()
            session.pop('discord_oauth', None)
            flash(_('Discord disconnected.'), 'success')
            return redirect(url_for('discord.settings'))
        if request.form.get('action') != 'connect' or not enabled() or account:
            abort(400)
        state = secrets.token_urlsafe(32)
        session['discord_oauth'] = dict(state=state, user_id=current_user.id, expires=int(time.time()) + 600)
        return redirect('https://discord.com/oauth2/authorize?' + urlencode(dict(
            client_id=current_app.config['DISCORD_APPLICATION_ID'], response_type='code', scope='identify',
            state=state, redirect_uri=site_url(url_for('discord.oauth_callback')))))
    response = current_app.make_response(render_template('auth/discord.html', form=form, account=account, enabled=enabled()))
    response.headers['Cache-Control'] = 'no-store'
    return response


@discord.get('/account/discord/callback')
@login_required
def oauth_callback():
    state = session.pop('discord_oauth', None)
    if (not state or state['user_id'] != current_user.id or state['expires'] < time.time()
            or not hmac.compare_digest(state['state'], request.args.get('state', ''))):
        abort(400)
    if request.args.get('error') or not request.args.get('code') or not enabled():
        flash(_('Discord connection was cancelled. Please try again.'), 'error')
        return redirect(url_for('discord.settings'))
    try:
        response = requests.post(API + '/oauth2/token', data=dict(
            client_id=current_app.config['DISCORD_APPLICATION_ID'],
            client_secret=current_app.config['DISCORD_CLIENT_SECRET'], grant_type='authorization_code',
            code=request.args['code'], redirect_uri=site_url(url_for('discord.oauth_callback'))), timeout=5)
        response.raise_for_status()
        token = response.json()['access_token']
        response = requests.get(API + '/users/@me', headers={'Authorization': 'Bearer ' + token}, timeout=5)
        response.raise_for_status()
        identity = response.json()
        if not snowflake(identity.get('id')):
            raise ValueError('Invalid identity')
        if (db.session.get(DiscordAccount, current_user.id)
                or DiscordAccount.query.filter_by(discord_id=identity['id']).first()):
            flash(_('An account is already connected. Disconnect it before linking again.'), 'error')
        else:
            db.session.add(DiscordAccount(user_id=current_user.id, discord_id=identity['id'],
                display_name=str(identity.get('global_name') or identity.get('username') or identity['id'])[:100]))
            db.session.commit()
            flash(_('Discord connected. Use /kw select in your party’s channel.'), 'success')
    except (requests.RequestException, ValueError, KeyError, TypeError, IntegrityError):
        db.session.rollback()
        # Do not log OAuth responses, codes or tokens.
        flash(_('Unable to connect Discord. Please try again.'), 'error')
    response = redirect(url_for('discord.settings'))
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    return response


@discord.post('/discord/interactions')
def interactions():
    public_key = current_app.config.get('DISCORD_PUBLIC_KEY')
    if not public_key or not current_app.config.get('DISCORD_APPLICATION_ID'):
        abort(503)
    if request.content_length and request.content_length > 65536:
        abort(413)
    from nacl.exceptions import BadSignatureError
    from nacl.signing import VerifyKey
    timestamp = request.headers.get('X-Signature-Timestamp', '')
    try:
        if abs(time.time() - int(timestamp)) > 300:
            abort(401)
        raw = request.get_data()
        if len(raw) > 65536:
            abort(413)
        VerifyKey(bytes.fromhex(public_key)).verify(timestamp.encode() + raw,
            bytes.fromhex(request.headers.get('X-Signature-Ed25519', '')))
    except (ValueError, BadSignatureError):
        abort(401)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or payload.get('application_id') != current_app.config['DISCORD_APPLICATION_ID']:
        abort(400)
    if payload.get('type') == 1:
        return jsonify(type=1)
    if payload.get('type') not in (2, 4):
        return jsonify(reply('Unsupported interaction.'))
    member = payload.get('member')
    if not isinstance(member, dict) or not isinstance(member.get('user'), dict):
        return jsonify(reply('Use Kettlewright commands in a server channel.'))
    discord_id = member['user'].get('id')
    if not all(snowflake(v) for v in (discord_id, payload.get('guild_id'), payload.get('channel_id'), payload.get('id'))):
        abort(400)
    limiter = current_app.extensions['discord_limiter']
    try:
        allowed = limiter.allow(discord_id, 'interaction', 40, 10)
    except Exception:
        return jsonify({'type': 8, 'data': {'choices': []}} if payload['type'] == 4
                       else reply('Commands are temporarily unavailable. Please try again.'))
    if not allowed:
        return jsonify({'type': 8, 'data': {'choices': []}} if payload['type'] == 4
                       else reply('Too many commands. Please wait a moment.'))
    account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if payload['type'] == 4:
        try:
            return jsonify(autocomplete(payload, account))
        except (TypeError, KeyError, AttributeError):
            abort(400)
    existing = db.session.get(DiscordInteraction, payload['id'])
    if existing:
        return jsonify(json.loads(existing.response))
    now = int(time.time())
    receipt = DiscordInteraction(id=payload['id'], discord_id=discord_id, created_at=now, response='{}')
    db.session.add(receipt)
    try:
        # Claim the ID before rolling; a duplicate request cannot roll a second time.
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return jsonify(json.loads(db.session.get(DiscordInteraction, payload['id']).response))
    notification = None
    try:
        with db.session.begin_nested():
            response, notification = execute(payload, account)
    except (ValueError, PermissionError) as error:
        response = reply(str(error))
    except (TypeError, KeyError, AttributeError):
        response = reply('Invalid command. Please use the command picker.')
    receipt.response = json.dumps(response)
    DiscordInteraction.query.filter(DiscordInteraction.created_at < now - 86400).delete()
    db.session.commit()
    if notification:
        publish_roll(*notification)
    return jsonify(response)


@discord.cli.command('register')
@click.option('--guild', help='Register immediately in one test server instead of globally.')
@click.option('--dry-run', is_flag=True, help='Print the command definition without contacting Discord.')
def register(guild, dry_run):
    """Create/update only /kw; leave other application commands intact."""
    definition = command_definition()
    if dry_run:
        click.echo(json.dumps(definition, indent=2))
        return
    app_id = current_app.config.get('DISCORD_APPLICATION_ID')
    token = current_app.config.get('DISCORD_BOT_TOKEN')
    if not snowflake(app_id) or not token or (guild is not None and not snowflake(guild)):
        raise click.ClickException('Configure DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN; use a numeric guild ID.')
    path = f'/applications/{app_id}' + (f'/guilds/{guild}' if guild else '') + '/commands'
    if guild:
        definition.pop('contexts')
        definition.pop('integration_types')
    try:
        response = requests.post(API + path, json=definition, headers={'Authorization': 'Bot ' + token}, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        raise click.ClickException('Discord command registration failed. Check credentials, access and network.') from None
    click.echo('Registered /kw' + (f' in server {guild}.' if guild else ' globally.'))


@discord.record_once
def init_limiter(state):
    from app import redis_url
    state.app.extensions['discord_limiter'] = SocketRateLimiter(redis_url)
