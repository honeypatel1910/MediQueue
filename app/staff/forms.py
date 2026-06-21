from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional


class StaffProfileForm(FlaskForm):
    job_title = StringField("Job title", validators=[Optional(), Length(max=120)])
    department = StringField("Department", validators=[Optional(), Length(max=120)])
    phone_extension = StringField("Phone extension", validators=[Optional(), Length(max=30)])
    submit = SubmitField("Update Staff Profile")
