from flask_wtf import FlaskForm
from wtforms import (Form, StringField, validators, SelectField, BooleanField,
                     DateTimeField, PasswordField, SubmitField, TextAreaField)

class LoginForm(FlaskForm):
    username = StringField()
    password = PasswordField()
    submit = SubmitField()
    
class PageForm(FlaskForm):
    owner = SelectField(choices=[])
    title = StringField()
    parent = SelectField(choices=[])
    template = SelectField(choices=[])
    is_published = BooleanField()
    content = TextAreaField()
    timestamp = DateTimeField()
    