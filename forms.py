from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired

class EditAnimeForm(FlaskForm):
    rating = StringField(label='Rating', validators=[DataRequired()])
    review = StringField(label='Write a short Review', validators=[DataRequired()])
    update_button = SubmitField(label='Update')

class AddAnimeForm(FlaskForm):
    title = StringField(label='Title of Anime', validators=[DataRequired()])
    add_button = SubmitField(label='Search Anime')

class CreateAnimeListForm(FlaskForm):
    name = StringField("Please name your list:", validators=[DataRequired()])
    add_button = SubmitField("Create List")

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register User")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")