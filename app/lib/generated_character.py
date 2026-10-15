"""Persist the reviewed Tools character snapshot without rerolling its contents."""
import re

from flask import current_app
from flask_babel import _
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer


def snapshot_signer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='tools-character-snapshot-v1')


def sign_snapshot(data):
    return snapshot_signer().dumps({'owner_id':current_user.id if current_user.is_authenticated else None, 'data':data})


def read_snapshot(token):
    payload = snapshot_signer().loads(token, max_age=24 * 60 * 60)
    if payload['owner_id'] != current_user.id:
        raise ValueError('This character preview belongs to another user.')
    return payload['data']


def character_markdown(data):
    sections = [f"**{_('Background')}:** {data['background']}",
        f"{data['hp']} HP · {data['strength']} STR · {data['dexterity']} DEX · {data['willpower']} WIL · {data['armor']} {_('Armor')} · {data['gold']} {_('Gold')}"]
    for key, label in [('description',_('Description')),('traits',_('Traits')),('bonds',_('Bonds')),('omens',_('Omens')),('scars',_('Scars')),('notes',_('Notes'))]:
        if data.get(key):
            sections.append(f"## {label}\n\n{data[key]}")
    for index in (1, 2):
        question, answer = data.get(f'background_table{index}_question'), data.get(f'background_table{index}_answer')
        if question or answer:
            sections.append(f"## {question or _('Background')}\n\n{answer or ''}")
    sections.append(f"## {_('Inventory')}")
    for container in data['containers']:
        items = []
        for item in data['items']:
            if item.get('location') != container['id']:
                continue
            details = list(item.get('tags', []))
            for field in ('uses', 'charges'):
                if field in item:
                    details.append(f"{item[field]} {_(field)}")
            text = item['name'] + (f" ({', '.join(details)})" if details else '')
            if item.get('description'):
                text += f" — {item['description']}"
            items.append(f'- {text}')
        sections.append(f"### {container['name']} ({container['slots']} {_('slots')})\n\n" + '\n'.join(items))
    for pet in data.get('pets', []):
        sections.append(f"## {_('Pets')}: {pet['name']}\n\n" + character_pet_markdown(pet))
    return '\n\n'.join(sections)


def character_pet_markdown(pet):
    stats = ' · '.join(f"{pet[field]} {label}" for field, label in [('hp','HP'),('strength','STR'),('dexterity','DEX'),('willpower','WIL')]
                       if pet.get(field) is not None)
    equipment = '\n'.join(f"- {item['name']}" for item in pet.get('items', []))
    return '\n\n'.join(part for part in [stats, pet.get('attack'), pet.get('notes'), equipment] if part)


def as_party_monster(party, data):
    from app.lib.companions import import_pet
    attacks = []
    for item in data['items']:
        damage = [tag for tag in item.get('tags', []) if re.fullmatch(r'd\d+(?:\+d\d+)*', tag)]
        if damage:
            attacks.append(f"{item['name']} ({', '.join(damage)})")
    # Armor on equipment is already counted by Companion.armorValue().
    monster = import_pet(dict(data, role=data['background'], armor=0,
        attack='; '.join(attacks)[:200], notes=character_markdown(data), custom_image=False))
    monster.kind, monster.party, monster.shared = 'monster', party, False
    monster.pets.extend(import_pet(pet) for pet in data.get('pets', []))
    return monster
