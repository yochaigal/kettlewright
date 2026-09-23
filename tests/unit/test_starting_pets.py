import json
from types import SimpleNamespace

import pytest
from app.lib.companions import starting_pets, catalog
from app.lib.data import load_backgrounds
from app.lib.char_utils import generate_character
from app.blueprints.generator import parse_character


@pytest.mark.parametrize('background,table,index,name', [
    ('Half Witch','table1',3,'Raven Familiar'), ('Prowler','table1',4,'Hollow Wolf'),
    ('Half Witch','table1',2,'Living Nightmare'), ('Aurifex','table1',1,'Dematerialized Pet'),
    ('Aurifex','table2',5,'Homunculus'), ('Kettlewright','table2',5,'Carrion Cat'),
    ('Kettlewright','table1',5,'Donkey'), ('Bonekeeper','table1',3,'Donkey'),
    ('Mountebank','table2',5,'Alchemical Tattoo'),
    *[('Outrider','table2',i,name) for i,name in enumerate(
      ['Heavy Destrier','Blacklegged Dandy','Rivertooth','Piebald Cob','Linden White','Stray Fogger'])],
])
def test_every_explicit_pet_reward(app_with_babel, background, table, index, name):
    with app_with_babel.test_request_context('/'):
        option = load_backgrounds()[background][table]['options'][index]
        parent = SimpleNamespace(hp=4,hp_max=4,strength=10,strength_max=10,dexterity=11,dexterity_max=11,willpower=12,willpower_max=12)
        pets = starting_pets(parent,[option,option])
        assert len(pets) == 1
        pet = pets[0]
        assert pet.name == name
        if name == 'Living Nightmare': assert pet.hp == 4 and pet.willpower == 12
        else: assert pet.hp == catalog('pet')[name].get('hp')


def test_generator_json_and_print_parser_keep_starting_mount(app_with_babel):
    with app_with_babel.test_request_context('/'):
        generated, raw = generate_character('Outrider')
        data = json.loads(raw)
        assert data['pets'][0]['name'] == generated.table2.option['pets'][0]
        character = parse_character(data)
        assert len(character.pets) == 1
        assert json.loads(character.toJSON())['pets'] == data['pets']


def test_no_pet_for_unrelated_options(app_with_babel):
    with app_with_babel.test_request_context('/'):
        assert starting_pets(SimpleNamespace(), [None, {'description':'Raven Familiar'}]) == []
