from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SubmitField
from wtforms.validators import Length, Optional


class PatientProfileForm(FlaskForm):
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    date_of_birth = DateField("Date of birth", validators=[Optional()], format="%Y-%m-%d")
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Update Profile")
