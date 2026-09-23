import hashlib
import hmac
import secrets
import time

from flask import current_app
from app.models import db, MFAChallenge

LIFETIME = 600
COOLDOWN = 60
MAX_ATTEMPTS = 5


def digest(value):
    return hmac.new(current_app.config['SECRET_KEY'].encode(), value.encode(), hashlib.sha256).hexdigest()


def binding(user):
    return digest(f'{user.id}:{user.email}:{user.password_hash}:{bool(user.mfa_enabled)}')


def issue_challenge(user, purpose):
    now = int(time.time())
    old = db.session.get(MFAChallenge, user.id)
    if old and now - old.sent_at < COOLDOWN:
        return None
    nonce = secrets.token_urlsafe(32)
    code = f'{secrets.randbelow(1000000):06d}'
    values = dict(nonce=nonce, code_hash=digest(nonce + ':' + code), binding=binding(user),
                  purpose=purpose, expires=now + LIFETIME, sent_at=now, attempts=0)
    if old:
        changed = MFAChallenge.query.filter_by(user_id=user.id).filter(
            MFAChallenge.sent_at <= now - COOLDOWN).update(values, synchronize_session=False)
        if not changed:
            db.session.rollback()
            return None
    else:
        db.session.add(MFAChallenge(user_id=user.id, **values))
    from sqlalchemy.exc import IntegrityError
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None
    from app.email import send_email
    try:
        send_email(user.email, 'Kettlewright verification code', 'auth/email/mfa',
                   code=code, user=user, synchronous=True)
    except Exception:
        MFAChallenge.query.filter_by(user_id=user.id, nonce=nonce).delete()
        db.session.commit()
        current_app.logger.warning('Unable to deliver MFA email')
        raise ValueError('Unable to send a verification code. Please try again.') from None
    return nonce


def pending_challenge(nonce):
    challenge = MFAChallenge.query.filter_by(nonce=nonce).first() if nonce else None
    if (not challenge or challenge.expires <= int(time.time()) or
            challenge.attempts >= MAX_ATTEMPTS or challenge.binding != binding(challenge.user)):
        return None
    return challenge


def consume_challenge(nonce, code):
    challenge = pending_challenge(nonce)
    if challenge is None:
        return None
    # The counter and one-time consumption live in the database, not a replayable cookie.
    changed = MFAChallenge.query.filter_by(nonce=nonce).filter(
        MFAChallenge.attempts < MAX_ATTEMPTS, MFAChallenge.expires > int(time.time())
    ).update({MFAChallenge.attempts: MFAChallenge.attempts + 1}, synchronize_session=False)
    if not changed:
        db.session.rollback()
        return None
    if not hmac.compare_digest(challenge.code_hash, digest(nonce + ':' + code)):
        db.session.commit()
        return None
    user, purpose = challenge.user, challenge.purpose
    removed = MFAChallenge.query.filter_by(nonce=nonce).delete(synchronize_session=False)
    if not removed:
        db.session.rollback()
        return None
    if purpose in ('enable', 'disable'):
        user.mfa_enabled = purpose == 'enable'
    db.session.commit()
    return user, purpose
