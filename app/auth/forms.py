from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models import User


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class RegistrationForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Retype password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create patient account")

    def validate_email(self, email):
        existing_user = User.query.filter_by(email=email.data.lower().strip()).first()
        if existing_user:
            raise ValidationError("An account with this email already exists.")


class PasswordResetRequestForm(FlaskForm):
    email = StringField("Registered email address", validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField("Send reset OTP")


class PasswordResetVerifyForm(FlaskForm):
    email = StringField("Registered email address", validators=[DataRequired(), Email(), Length(max=255)])
    otp = StringField("6-digit OTP", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Verify OTP")


class PasswordResetConfirmForm(FlaskForm):
    email = StringField("Registered email address", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("New password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Retype new password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Reset password")
