"""Mounts (#537): a pet that carries for its owner (a character, or a hireling).

A mount's slots are a container in its owner's inventory, linked to it ({'mount': pet id}), and the pet keeps no
inventory of its own: one place for what it carries, so nothing is out of step. The link stays in sync:

- renaming the pet renames its container, and renaming the container renames the pet;
- deleting the pet takes its container away (what it carried goes to the main inventory);
- removing the container leaves a plain pet, which gets its slots back (empty).

A pet that can carry is one whose catalog entry has slots (Horse, Mule, the Outrider's mounts). Adding one offers to
make it carry; an Outrider's background mount, which also gives the character a container of its name, is linked to
that container when the character is saved (link_mounts).
"""
import json

from app.models import db


def owner_of(pet):
    return pet.character or pet.hireling


def _containers(owner):
    try:
        containers = json.loads(owner.containers or '[]')
    except (TypeError, ValueError):
        return []
    return containers if isinstance(containers, list) else []


def mount_container(pet):
    """The container in its owner's inventory this pet carries, or None."""
    owner = owner_of(pet)
    if owner is None or pet.id is None:
        return None
    return next((c for c in _containers(owner) if isinstance(c, dict) and c.get('mount') == pet.id), None)


def own_slots(pet):
    """The slots of the pet's own main inventory."""
    return next((int(c.get('slots') or 0) for c in _containers(pet) if c.get('id') == 0), 0)


def _set_own_slots(pet, slots):
    containers = _containers(pet) or [{'id': 0, 'name': 'Main', 'slots': 0}]
    for container in containers:
        if container.get('id') == 0:
            container['slots'] = slots
    pet.containers = json.dumps(containers)


def carry(pet, owner, container=None):
    """The pet carries for its owner: its slots become a container (or this one of the owner's), linked to it."""
    if pet.id is None:
        db.session.flush()
    containers = _containers(owner)
    if container is None:
        slots = own_slots(pet)
        if slots <= 0:
            return None
        container = {'name': pet.name, 'slots': slots, 'id': max((c.get('id', 0) for c in containers), default=0) + 1}
        containers.append(container)
    else:
        container = next(c for c in containers if c.get('id') == container['id'])
    container['mount'] = pet.id
    owner.containers = json.dumps(containers)
    _set_own_slots(pet, 0)
    return container


def link_mounts(owner):
    """Link each of the owner's pets that can carry, and isn't linked yet, to the container of its name that nothing
    else carries: an Outrider's background mount, a pet imported with its owner. Only a pet with nothing of its own
    (its inventory empty), so no item is ever in two places."""
    if not owner.pets:
        return
    db.session.flush()
    containers = _containers(owner)
    linked = {c.get('mount') for c in containers if c.get('mount') is not None}
    pets = {pet.id for pet in owner.pets}
    for container in containers:  # A link to a pet this owner doesn't have (an imported one's old id) goes.
        if container.get('mount') is not None and container['mount'] not in pets:
            container.pop('mount')
    owner.containers = json.dumps(containers)
    for pet in owner.pets:
        if pet.id in linked or json.loads(pet.items or '[]') or own_slots(pet) <= 0:
            continue
        match = next((c for c in _containers(owner) if c.get('name') == pet.name and c.get('mount') is None
                      and c.get('id') != 0 and not c.get('carried_by') and not c.get('on_the_ground')), None)
        if match is not None:
            carry(pet, owner, match)


def renamed_pet(pet):
    """The pet has a new name: so has its container."""
    container = mount_container(pet)
    if container is None:
        return
    owner = owner_of(pet)
    containers = _containers(owner)
    for c in containers:
        if c.get('mount') == pet.id:
            c['name'] = pet.name
    owner.containers = json.dumps(containers)


def renamed_container(owner, container):
    """A mount's container has a new name: so has the mount."""
    pet = next((p for p in owner.pets if p.id == container.get('mount')), None) if container.get('mount') else None
    if pet is not None:
        pet.name = container['name'][:100]


def container_removed(owner, container):
    """The owner removed a mount's container: the pet is a plain pet again, with its slots (empty)."""
    pet = next((p for p in owner.pets if p.id == container.get('mount')), None) if container.get('mount') else None
    if pet is not None:
        _set_own_slots(pet, int(container.get('slots') or 0))


def pet_removed(pet):
    """The pet goes: so does its container, and what it carried goes to its owner's main inventory."""
    container = mount_container(pet)
    if container is None:
        return
    from app.lib.inventory import Inventory
    Inventory(owner_of(pet)).delete_container(container['id'], 0)


def can_carry(template):
    """Whether a catalog pet can carry for its owner (it has slots)."""
    return bool((template or {}).get('slots'))

