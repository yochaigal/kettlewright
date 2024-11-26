from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, HiddenField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, Email, Regexp, EqualTo, URL, ValidationError
import os
import json


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()], render_kw={"placeholder": "email"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={
                             "placeholder": "password"})
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message='Invalid email address')], render_kw={"placeholder": "email"})

    # user_name = StringField('Username', validators=[DataRequired(), Length(
    #     1, 64)], render_kw={"placeholder": "username"})
    user_name = StringField('Username', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              'Usernames must have only letters, '
                                              'numbers, dots or underscores')],
        render_kw={"placeholder": "username"})
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(8, 64, message='Password must be between 8 and 64 characters'), EqualTo('password2', message='Passwords must match')],
                             render_kw={"placeholder": "password"},)
    password2 = PasswordField('Confirm password', validators=[DataRequired()],
                              render_kw={"placeholder": "confirm password"})
    signup_code = StringField('Signup Code', validators=[DataRequired()],
                              render_kw={"placeholder": "signup code"})
    submit = SubmitField('Sign Up')

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
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()], render_kw={"placeholder": "email"})
    submit = SubmitField('Reset Password')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
                             DataRequired(), EqualTo('password2', message='Passwords must match')],
                             render_kw={"placeholder": "password"})
    password2 = PasswordField('Confirm password', validators=[
                              DataRequired()], render_kw={"placeholder": "confirm password"})
    submit = SubmitField('Reset Password')


class ResendConfirmationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message='Invalid email address')], render_kw={"placeholder": "email"})
    submit = SubmitField('Resend Confirmation')


class EmailUpdateForm(FlaskForm):
    password = PasswordField('Password', validators=[
                             DataRequired()],
                             render_kw={"placeholder": "Password"})
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(), EqualTo('email2', message='Email addresses must match')], render_kw={"placeholder": "new email"})
    email2 = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                              Email()], render_kw={"placeholder": "confirm new email"})
    submit1 = SubmitField('Change')


class PasswordUpdateForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[
        DataRequired()], render_kw={"placeholder": "current password"})
    password = PasswordField('New password', validators=[
                             DataRequired(), EqualTo('password2', message='Passwords must match')],
                             render_kw={"placeholder": "new password"})
    password2 = PasswordField('Confirm new password', validators=[
                              DataRequired()], render_kw={"placeholder": "confirm new password"})
    submit2 = SubmitField('Change')


json_file_path = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), 'static', 'json', 'backgrounds', 'background_data.json')


def load_data_from_json(file_path):
    with open(file_path, 'r') as file:
        backgrounds_data = json.load(file)

    names_choices = [('', 'Name (d10)...')]
    background_choices = [('', 'Background (d20)...')]

    for background, data in backgrounds_data.items():
        # Extracting names
        for name in data["names"]:
            names_choices.append((name, name))

        # Adding background to choices
        background_choices.append((background, background))

    background_choices.append(('Custom', '** Custom **'))
    names_choices.append(('Custom', '** Custom **'))
    return names_choices, background_choices


name_choices, background_choices = load_data_from_json(json_file_path)


class CharacterForm(FlaskForm):

    background = SelectField(
        'Background', validators=[DataRequired()], choices=background_choices, id="background-field")
    name = SelectField('Name', choices=name_choices, id="name-field")
    # name = SelectField(
    #     'Name', validators=[DataRequired()], choices=[('', 'Choose or Roll Name (d10)...'), ('Hestia', 'Hestia')], id="name-field")
    custom_background = StringField('Custom Background', validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": "Custom Background"})

    # def validate_custom_background(self, field):
    #     if field.data:
    #         field.data = bleach.clean(field.data)
    #     else:
    #         field.data = ''

    custom_name = StringField('Custom Name', validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": "Custom Name"})

    # def validate_custom_name(self, field):
    #     if field.data:
    #         field.data = bleach.clean(field.data)
    #     else:
    #         field.data = ''
    strength = IntegerField('Strength')
    strength_max = IntegerField('Strength Max', validators=[InputRequired()])
    dexterity = IntegerField('Strength')
    dexterity_max = IntegerField('Strength Max', validators=[InputRequired()])
    willpower = IntegerField('Willpower')
    willpower_max = IntegerField('Willpower Max', validators=[InputRequired()])
    hp = IntegerField('HP')
    hp_max = IntegerField('HP Max', validators=[InputRequired()])
    items = HiddenField()
    description = StringField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "description"})
    traits = HiddenField()
    notes = HiddenField()
    bonds = HiddenField()
    omens = HiddenField()
    gold = IntegerField('Gold')
    submit = SubmitField('Save Character')
    containers = HiddenField()
    image_url = HiddenField()
    custom_image = HiddenField()
    armor = HiddenField()


class CharacterEditForm(FlaskForm):
    name = StringField('Custom Name', validators=[DataRequired(), Length(
        1, 32)])
    strength = IntegerField('Strength', validators=[InputRequired()])
    strength_max = IntegerField('Strength Max', validators=[InputRequired()])
    dexterity = IntegerField('Dexterity', validators=[InputRequired()])
    dexterity_max = IntegerField('Dexterity Max', validators=[InputRequired()])
    willpower = IntegerField('Willpower', validators=[InputRequired()])
    willpower_max = IntegerField('Willpower Max', validators=[InputRequired()])
    hp = IntegerField('Willpower', validators=[InputRequired()])
    hp_max = IntegerField('Willpower Max', validators=[InputRequired()])
    gold = IntegerField('Gold', validators=[InputRequired()])
    submit = SubmitField('Save')
    items = HiddenField()
    containers = HiddenField()
    deprived = BooleanField('Deprived')
    notes = TextAreaField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "notes"})
    description = TextAreaField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "description"})
    traits = TextAreaField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "traits"})
    bonds = TextAreaField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "bonds"})
    omens = TextAreaField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "omens"})
    scars = TextAreaField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "scars"})
    image_url = HiddenField()
    custom_image = HiddenField()
    armor = HiddenField()
    party_code = StringField('Party Code', validators=[Length(
        0, 32)], render_kw={"placeholder": "join code"})
    transfer = HiddenField()


# Text field partial forms
class CharacterEditFormNotes(FlaskForm):
    notes = TextAreaField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "notes"})
    
class CharacterEditFormDescription(FlaskForm):
    description = TextAreaField('Description', validators=[Length(
        0, 2000)], render_kw={"placeholder": "description"})
    
class CharacterEditFormTraits(FlaskForm):    
    traits = TextAreaField('Traits', validators=[Length(
        0, 2000)], render_kw={"placeholder": "traits"})

class CharacterEditFormBonds(FlaskForm):    
    bonds = TextAreaField('Bonds', validators=[Length(
        0, 2000)], render_kw={"placeholder": "bonds"})
    
class CharacterEditFormOmens(FlaskForm):    
    omens = TextAreaField('Omens', validators=[Length(
        0, 2000)], render_kw={"placeholder": "omens"})

class CharacterEditFormParty(FlaskForm):
    party_code = StringField('Party Code', validators=[Length(0, 32)], render_kw={"placeholder": "join code"})

class CharacterEditFormScars(FlaskForm):
    scars = TextAreaField('Scars', validators=[Length(0, 2000)], render_kw={"placeholder": "scars"})
    
class CharacterEditFormName(FlaskForm):
    name = StringField('Custom Name', validators=[DataRequired(), Length(1, 32)])
    

class CharacterJSONForm(FlaskForm):
    name = HiddenField('Name', validators=[DataRequired(), Length(max=2000)])
    background = HiddenField('Background', validators=[
                             DataRequired(), Length(max=2000)])
    custom_name = HiddenField('Custom Name', validators=[Length(max=2000)])
    custom_background = HiddenField(
        'Custom Background', validators=[Length(max=2000)])

    # Integer fields
    strength = HiddenField('Strength', validators=[
                           InputRequired(), Length(max=10)])
    strength_max = HiddenField('Strength Max', validators=[
                               InputRequired(), Length(max=10)])
    dexterity = HiddenField('Dexterity', validators=[
                            InputRequired(), Length(max=10)])
    dexterity_max = HiddenField('Dexterity Max', validators=[
                                InputRequired(), Length(max=10)])
    willpower = HiddenField('Willpower', validators=[
                            InputRequired(), Length(max=10)])
    willpower_max = HiddenField('Willpower Max', validators=[
                                InputRequired(), Length(max=10)])
    hp = HiddenField('HP', validators=[InputRequired(), Length(max=10)])
    hp_max = HiddenField('HP Max', validators=[
                         InputRequired(), Length(max=10)])
    gold = HiddenField('Gold', validators=[InputRequired(), Length(max=10)])

    items = HiddenField('Items', validators=[Length(max=100000)])
    containers = HiddenField('Containers', validators=[Length(max=100000)])

    # Boolean field - allowing "true" or "false" (5 characters max)
    deprived = HiddenField('Deprived', validators=[Length(max=5)])

    notes = HiddenField('Notes', validators=[Length(max=2000)])
    description = HiddenField('Description', validators=[Length(max=2000)])
    traits = HiddenField('Traits', validators=[Length(max=2000)])
    bonds = HiddenField('Bonds', validators=[Length(max=2000)])
    omens = HiddenField('Omens', validators=[Length(max=2000)])
    scars = HiddenField('Scars', validators=[Length(max=2000)])

    image_url = HiddenField('Image URL', validators=[Length(max=2000)])
    custom_image = HiddenField('Custom Image', validators=[Length(max=2000)])
    armor = HiddenField('Armor', validators=[Length(max=2000)])

    submit = SubmitField('Save')


class PartyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": "name"})
    description = TextAreaField('Description', validators=[Length(
        0, 2000)], render_kw={"placeholder": "description"})
    notes = StringField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "notes"})
    submit = SubmitField('Save Party')


class PartyEditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(
        1, 32)], render_kw={"placeholder": "name"})
    description = TextAreaField('Description', validators=[Length(
        0, 2000)], render_kw={"placeholder": "description"})
    notes = StringField('Notes', validators=[Length(
        0, 2000)], render_kw={"placeholder": "notes"})
    members = HiddenField('HiddenString')
    items = HiddenField()
    containers = HiddenField()
    transfer = HiddenField()
    events = HiddenField()
    version = HiddenField('Version')
