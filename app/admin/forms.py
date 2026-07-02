from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from app.models import User


class AdminUserCreateForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
    role_id = SelectField("Role", coerce=int, validators=[DataRequired()])
    password = PasswordField("Temporary password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm temporary password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    active = BooleanField("Account active", default=True)

    phone = StringField("Patient phone", validators=[Optional(), Length(max=30)])
    address = StringField("Patient address", validators=[Optional(), Length(max=255)])

    job_title = StringField("Staff job title", validators=[Optional(), Length(max=120)])
    department = StringField("Department", validators=[Optional(), Length(max=120)])
    phone_extension = StringField("Phone extension", validators=[Optional(), Length(max=30)])
    register_name = StringField("Register name", validators=[Optional(), Length(max=50)])
    registration_number = StringField("Registration number", validators=[Optional(), Length(max=80)])
    verified = BooleanField("Professional registration verified", default=True)

    submit = SubmitField("Create User")

    def validate_email(self, field):
        existing_user = User.query.filter_by(email=field.data.lower().strip()).first()
        if existing_user:
            raise ValidationError("An account with this email already exists.")


class AdminPrescriptionCollectionForm(FlaskForm):
    status = SelectField(
        "Collection status",
        choices=[
            ("Ready for Collection", "Ready for Collection"),
            ("Collected", "Collected"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Status")
