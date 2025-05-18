from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, InputRequired

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(),
        Regexp(r'^[\w\.-]+@[\w\.-]+\.\w+$', message="Invalid email format")
    ])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired(), Length(min=2)])
    email = StringField("Email", validators=[
        DataRequired(),
        Regexp(r'^[\w\.-]+@[\w\.-]+\.\w+$', message="Invalid email format")
    ])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Register")
