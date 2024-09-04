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
    submit = SubmitField('Register')

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


class CharacterJSONForm(FlaskForm):

    name = HiddenField('HiddenString', validators=[DataRequired()])
    background = HiddenField('HiddenString', validators=[DataRequired()])
    custom_name = HiddenField('HiddenString')
    custom_background = HiddenField('HiddenString')

    strength = HiddenField('HiddenNumber', validators=[InputRequired()])
    strength_max = HiddenField('HiddenNumber', validators=[InputRequired()])
    dexterity = HiddenField('HiddenNumber', validators=[InputRequired()])
    dexterity_max = HiddenField('HiddenNumber', validators=[InputRequired()])
    willpower = HiddenField('HiddenNumber', validators=[InputRequired()])
    willpower_max = HiddenField('HiddenNumber', validators=[InputRequired()])
    hp = HiddenField('HiddenNumber', validators=[InputRequired()])
    hp_max = HiddenField('HiddenNumber', validators=[InputRequired()])
    gold = HiddenField('HiddenNumber', validators=[InputRequired()])
    items = HiddenField('HiddenString')
    containers = HiddenField('HiddenString')
    deprived = HiddenField('HiddenBoolean')
    notes = HiddenField('HiddenString')
    description = HiddenField('HiddenString')
    bonds = HiddenField('HiddenString')
    omens = HiddenField('HiddenString')
    scars = HiddenField('HiddenString')
    image_url = HiddenField('HiddenString')
    custom_image = HiddenField('HiddenBoolean')

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
