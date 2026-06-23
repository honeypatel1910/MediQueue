from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class StaffProfileForm(FlaskForm):
    job_title = StringField("Job title", validators=[Optional(), Length(max=120)])
    department = StringField("Department", validators=[Optional(), Length(max=120)])
    phone_extension = StringField("Phone extension", validators=[Optional(), Length(max=30)])
    submit = SubmitField("Update Staff Profile")


class AvailabilityForm(FlaskForm):
    available_date = DateField("Date", validators=[DataRequired()])
    start_time = TimeField("Start time", validators=[DataRequired()])
    end_time = TimeField("End time", validators=[DataRequired()])
    slot_duration_minutes = IntegerField(
        "Slot duration in minutes",
        default=20,
        validators=[DataRequired(), NumberRange(min=10, max=60)],
    )
    location = StringField("Location", default="GP Practice", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Create Availability")

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("End time must be later than start time.")
