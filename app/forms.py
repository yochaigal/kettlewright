from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, HiddenField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, Email, Regexp, EqualTo, URL, ValidationError
import os
import json
from flask_babel import lazy_gettext as _l
from flask_babel import _


class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Length(1, 64),
                                             Email()], render_kw={"placeholder": "email"})
    password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={
                             "placeholder": "password"})
    remember_me = BooleanField(_l('Keep me logged in'))
    submit = SubmitField(_l('Login'))


class RegistrationForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Length(1, 64),
                                             Email(message=_l('Invalid email address'))], render_kw={"placeholder": _l("email")})

    # user_name = StringField('Username', validators=[DataRequired(), Length(
    #     1, 64)], render_kw={"placeholder": "username"})
    user_name = StringField(_l('Username'), validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              'Usernames must have only letters, '
                                              'numbers, dots or underscores')],
        render_kw={"placeholder": _l("username")})
    password = PasswordField(_l('Password'), validators=[
                             DataRequired(), Length(8, 64, message=_l('Password must be between 8 and 64 characters')), EqualTo('password2', message=_l('Passwords must match'))],
                             render_kw={"placeholder": _l("password")},)
    password2 = PasswordField(_l('Confirm password'), validators=[DataRequired()],
                              render_kw={"placeholder": _l("confirm password")})
    signup_code = StringField(_l('Signup Code'), validators=[DataRequired()],
                              render_kw={"placeholder": _l("signup code")})
    submit = SubmitField(_l('Sign Up'))
    captcha_token = HiddenField('captcha_token')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        require_signup_code = os.environ.get(
            'REQUIRE_SIGNUP_CODE', 'False').lower() == 'true'
        if not require_signup_code:
            del self.signup_code

    def validate_signup_code(self, field):
        if os.environ.get('REQUIRE_SIGNUP_CODE', 'False').lower() == 'true':
            correct_code = os.environ.get('SIGNUP_CODE', 'default')
            if field.data != correct_code:
                raise ValidationError('Invalid signup code')


class PasswordResetRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Length(1, 64),
                                             Email()], render_kw={"placeholder": "email"})
    submit = SubmitField(_l('Reset Password'))


class PasswordResetForm(FlaskForm):
    password = PasswordField(_l('New Password'), validators=[
                             DataRequired(), EqualTo('password2', message=_l('Passwords must match'))],
                             render_kw={"placeholder": _l("password")})
    password2 = PasswordField(_l('Confirm password'), validators=[
                              DataRequired()], render_kw={"placeholder": _l("confirm password")})
    submit = SubmitField(_l('Reset Password'))


class ResendConfirmationForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Length(1, 64),
                                             Email(message=_l('Invalid email address'))], render_kw={"placeholder": _l("email")})
    submit = SubmitField(_l('Resend Confirmation'))


class EmailUpdateForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[
                             DataRequired()],
                             render_kw={"placeholder": _l("password")})
    email = StringField(_l('Email'), validators=[DataRequired(), Length(1, 64),
                                             Email(), EqualTo('email2', message=_l('Email addresses must match'))], render_kw={"placeholder": _l("new email")})
    email2 = StringField(_l('Email'), validators=[DataRequired(), Length(1, 64),
                                              Email()], render_kw={"placeholder": _l("confirm new email")})
    submit1 = SubmitField(_l('Change'))


class PasswordUpdateForm(FlaskForm):
    old_password = PasswordField(_l('Current Password'), validators=[
        DataRequired()], render_kw={"placeholder": _l("current password")})
    password = PasswordField(_l('New password'), validators=[
                             DataRequired(), EqualTo('password2', message=_l('Passwords must match'))],
                             render_kw={"placeholder": _l("new password")})
    password2 = PasswordField(_l('Confirm new password'), validators=[
                              DataRequired()], render_kw={"placeholder": _l("confirm new password")})
    submit2 = SubmitField(_l('Change'))


json_file_path = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), 'static', 'json', 'backgrounds', 'background_data.json')


def load_data_from_json(file_path):
    with open(file_path, 'r') as file:
        backgrounds_data = json.load(file)

    names_choices = [('', _l('Name (d10)...'))]
    background_choices = [('', _l('Background (d20)...'))]

    for background, data in backgrounds_data.items():
        # Extracting names
        for name in data["names"]:
            names_choices.append((name, name))

        # Adding background to choices
        background_choices.append((background, _l(background)))

    background_choices.insert(1, ('Custom', _l('** Custom **') ))
    names_choices.insert(1, ('Custom', _l('** Custom **')))
    return names_choices, background_choices


name_choices, background_choices = load_data_from_json(json_file_path)


class CharacterForm(FlaskForm):

    background = SelectField(
        _l('Background'), validators=[DataRequired()], choices=background_choices, id="background-field")
    name = SelectField(_l('Name'), choices=name_choices, id="name-field")
    # name = SelectField(
    #     'Name', validators=[DataRequired()], choices=[('', 'Choose or Roll Name (d10)...'), ('Hestia', 'Hestia')], id="name-field")
    custom_background = StringField(_l('Custom Background'), validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": _l("Custom Background")})

    # def validate_custom_background(self, field):
    #     if field.data:
    #         field.data = bleach.clean(field.data)
    #     else:
    #         field.data = ''

    custom_name = StringField(_l('Custom Name'), validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": _l("Custom Name")})

    # def validate_custom_name(self, field):
    #     if field.data:
    #         field.data = bleach.clean(field.data)
    #     else:
    #         field.data = ''
    strength = IntegerField(_l('Strength'))
    strength_max = IntegerField(_l('Strength Max'), validators=[DataRequired()])
    dexterity = IntegerField(_l('Dexterity'))
    dexterity_max = IntegerField(_l('Dexterity Max'), validators=[InputRequired()])
    willpower = IntegerField(_l('Willpower'))
    willpower_max = IntegerField(_l('Willpower Max'), validators=[InputRequired()])
    hp = IntegerField(_l('HP'))
    hp_max = IntegerField(_l('HP Max'), validators=[InputRequired()])
    items = HiddenField()
    description = StringField(_l('Notes'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("description")})
    traits = HiddenField()
    notes = HiddenField()
    bonds = HiddenField()
    omens = HiddenField()
    gold = IntegerField(_l('Gold'))
    submit = SubmitField(_l('Save Character'))
    containers = HiddenField()
    image_url = HiddenField()
    custom_image = HiddenField()
    armor = HiddenField()


class CharacterEditForm(FlaskForm):
    name = StringField(_l('Custom Name'), validators=[DataRequired(), Length(
        1, 32)])
    strength = IntegerField(_l('Strength'), validators=[InputRequired()])
    strength_max = IntegerField(_l('Strength Max'), validators=[InputRequired()])
    dexterity = IntegerField(_l('Dexterity'), validators=[InputRequired()])
    dexterity_max = IntegerField(_l('Dexterity Max'), validators=[InputRequired()])
    willpower = IntegerField(_l('Willpower'), validators=[InputRequired()])
    willpower_max = IntegerField(_l('Willpower Max'), validators=[InputRequired()])
    hp = IntegerField(_l('Willpower'), validators=[InputRequired()])
    hp_max = IntegerField(_l('Willpower Max'), validators=[InputRequired()])
    gold = IntegerField(_l('Gold'), validators=[InputRequired()])
    submit = SubmitField(_l('Save'))
    items = HiddenField()
    containers = HiddenField()
    deprived = BooleanField(_l('Deprived'))
    notes = TextAreaField(_l('Notes'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("notes")})
    description = TextAreaField(_l('Description'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("description")})
    traits = TextAreaField(_l('Traits'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("traits")})
    bonds = TextAreaField(_l('Bonds'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("bonds")})
    omens = TextAreaField(_l('Omens'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("omens")})
    scars = TextAreaField(_l('Scars'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("scars")})
    image_url = HiddenField()
    custom_image = HiddenField()
    armor = HiddenField()
    party_code = StringField(_l('Party Code'), validators=[Length(
        0, 32)], render_kw={"placeholder": _l("join code")})
    transfer = HiddenField()


# Text field partial forms
class CharacterEditFormNotes(FlaskForm):
    notes = TextAreaField(_l('Notes'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("notes")})
    
class CharacterEditFormDescription(FlaskForm):
    description = TextAreaField(_l('Description'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("description")})
    
class CharacterEditFormTraits(FlaskForm):    
    traits = TextAreaField(_l('Traits'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("traits")})

class CharacterEditFormBonds(FlaskForm):    
    bonds = TextAreaField(_l('Bonds'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("bonds")})
    
class CharacterEditFormOmens(FlaskForm):    
    omens = TextAreaField(_l('Omens'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("omens")})

class CharacterEditFormParty(FlaskForm):
    party_code = StringField(_l('Party Code'), validators=[Length(0, 32)], render_kw={"placeholder": _l("join code")})

class CharacterEditFormScars(FlaskForm):
    scars = TextAreaField(_l('Scars'), validators=[Length(0, 2000)], render_kw={"placeholder": _l("scars")})
    
class CharacterEditFormName(FlaskForm):
    name = StringField(_l('Custom Name'), validators=[DataRequired(), Length(1, 32)])
    

class CharacterJSONForm(FlaskForm):
    name = HiddenField(_l('Name'), validators=[DataRequired(), Length(max=2000)])
    background = HiddenField(_l('Background'), validators=[
                             DataRequired(), Length(max=2000)])
    custom_name = HiddenField(_l('Custom Name'), validators=[Length(max=2000)])
    custom_background = HiddenField(
        _l('Custom Background'), validators=[Length(max=2000)])

    # Integer fields
    strength = HiddenField(_l('Strength'), validators=[
                           InputRequired(), Length(max=10)])
    strength_max = HiddenField(_l('Strength Max'), validators=[
                               InputRequired(), Length(max=10)])
    dexterity = HiddenField(_l('Dexterity'), validators=[
                            InputRequired(), Length(max=10)])
    dexterity_max = HiddenField(_l('Dexterity Max'), validators=[
                                InputRequired(), Length(max=10)])
    willpower = HiddenField(_l('Willpower'), validators=[
                            InputRequired(), Length(max=10)])
    willpower_max = HiddenField(_l('Willpower Max'), validators=[
                                InputRequired(), Length(max=10)])
    hp = HiddenField(_l('HP'), validators=[InputRequired(), Length(max=10)])
    hp_max = HiddenField(_l('HP Max'), validators=[
                         InputRequired(), Length(max=10)])
    gold = HiddenField(_l('Gold'), validators=[InputRequired(), Length(max=10)])

    items = HiddenField(_l('Items'), validators=[Length(max=100000)])
    containers = HiddenField(_l('Containers'), validators=[Length(max=100000)])

    # Boolean field - allowing "true" or "false" (5 characters max)
    deprived = HiddenField(_l('Deprived'), validators=[Length(max=5)])

    notes = HiddenField(_l('Notes'), validators=[Length(max=2000)])
    description = HiddenField(_l('Description'), validators=[Length(max=2000)])
    traits = HiddenField(_l('Traits'), validators=[Length(max=2000)])
    bonds = HiddenField(_l('Bonds'), validators=[Length(max=2000)])
    omens = HiddenField(_l('Omens'), validators=[Length(max=2000)])
    scars = HiddenField(_l('Scars'), validators=[Length(max=2000)])

    image_url = HiddenField(_l('Image URL'), validators=[Length(max=2000)])
    custom_image = HiddenField(_l('Custom Image'), validators=[Length(max=2000)])
    armor = HiddenField(_l('Armor'), validators=[Length(max=2000)])

    submit = SubmitField(_l('Save'))


class PartyForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": _l("name")})
    description = TextAreaField(_l('Description'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("description")})
    notes = StringField(_l('Notes'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("notes")})
    submit = SubmitField(_l('Save Party'))


class PartyEditForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": _l("name")})
    description = TextAreaField(_l('Description'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("description")})
    notes = StringField(_l('Notes'), validators=[Length(
        0, 2000)], render_kw={"placeholder": _l("notes")})
    members = HiddenField('HiddenString')
    items = HiddenField()
    containers = HiddenField()
    transfer = HiddenField()
    events = HiddenField()
    version = HiddenField('Version')
