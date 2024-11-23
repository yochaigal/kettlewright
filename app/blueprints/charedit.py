from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response
from app.models import db, User, Character
from app.forms import CharacterEditFormTraits, CharacterEditForm, CharacterEditFormDescription, CharacterEditFormBonds, CharacterEditFormOmens, CharacterEditFormNotes
from app.main import sanitize_data

character_edit = Blueprint('character_edit', __name__)
bool_fields = ['deprived']

@character_edit.route('/charedit/inplace-attrs/<username>/<url_name>')
def charedit_inplace_attrs(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    form = CharacterEditForm(obj=character)
    return render_template('partial/charedit_attrs.html', user=user, character=character, form=form, username=username, url_name=url_name)

@character_edit.route('/charedit/inplace-attrs/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_attrs_save(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    data = request.form
    for field in data:
        value = data[field]
        if field in bool_fields:
            if value == 'y':
                value = True
        setattr(character, field, value) # TODO: sanitize data
    # bool field disappears when unchecked
    for bf in bool_fields:
        if not bf in data:
            setattr(character, bf, False)
    db.session.commit()
    return render_template('partial/charview_attrs.html', user=user, character=character, username=username, url_name=url_name)

    
@character_edit.route('/charedit/inplace-attrs/<username>/<url_name>/cancel')
def charedit_inplace_attrs_cancel(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    return render_template('partial/charview_attrs.html', user=user, character=character, username=username, url_name=url_name)


@character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>', methods=['GET'])
def charedit_inplace_text(username, url_name, field_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    if field_name == "traits":
        form = CharacterEditFormTraits(obj=character)
        template = 'partial/charedit_traits.html'
    elif field_name == "description":
        form = CharacterEditFormDescription(obj=character)
        template = 'partial/charedit_description.html'
    elif field_name == "bonds":
        form = CharacterEditFormBonds(obj=character)
        template = 'partial/charedit_bonds.html'        
    elif field_name == "omens":
        form = CharacterEditFormOmens(obj=character)
        template = 'partial/charedit_omens.html'                
    elif field_name == "notes":
        form = CharacterEditFormNotes(obj=character)
        template = 'partial/charedit_notes.html'                

    return render_template(template, user=user, character=character, form=form, username=username, url_name=url_name)
    
@character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>/save', methods=['POST'])
def charedit_inplace_text_save(username, url_name, field_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    data = request.form
    setattr(character, field_name, sanitize_data(data[field_name]))
    db.session.commit()
    if field_name == "traits":
        template = 'partial/charview_traits.html'
    elif field_name == "description":
        template = 'partial/charview_description.html'
    elif field_name == "bonds":
        template = 'partial/charview_bonds.html'
    elif field_name == "omens":
        template = 'partial/charview_omens.html'        
    elif field_name == "notes":
        template = 'partial/charview_notes.html'        
    return render_template(template, user=user, character=character, username=username, url_name=url_name)

@character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>/cancel', methods=['GET'])
def charedit_inplace_text_cancel(username, url_name, field_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    if field_name == "traits":
        template = 'partial/charview_traits.html'
    elif field_name == "description":
        template = 'partial/charview_description.html'
    elif field_name == "bonds":
        template = 'partial/charview_bonds.html'        
    elif field_name == "omens":
        template = 'partial/charview_omens.html'                
    elif field_name == "notes":
        template = 'partial/charview_notes.html'                
    return render_template(template, user=user, character=character, username=username, url_name=url_name)