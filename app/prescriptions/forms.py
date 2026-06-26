from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


MEDICINE_CHOICES = [
    ("Paracetamol 500mg", "Paracetamol 500mg"),
    ("Ibuprofen 200mg", "Ibuprofen 200mg"),
    ("Cetirizine 10mg", "Cetirizine 10mg"),
    ("Omeprazole 20mg", "Omeprazole 20mg"),
    ("Amlodipine 5mg", "Amlodipine 5mg"),
    ("Salbutamol inhaler", "Salbutamol inhaler"),
]


class PrescriptionRequestForm(FlaskForm):
    medicine_name = SelectField("Medicine", choices=MEDICINE_CHOICES, validators=[DataRequired()])
    quantity = StringField("Quantity", validators=[DataRequired(), Length(max=80)])
    reason = TextAreaField("Reason", validators=[Length(max=255)])
    submit = SubmitField("Request Prescription")


class PrescriptionReviewForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("Requested", "Requested"),
            ("Under Review", "Under Review"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Prescription")


class PrescriptionPaymentForm(FlaskForm):
    payment_method = SelectField(
        "Payment method",
        choices=[
            ("Debit Card", "Debit Card"),
            ("Credit Card", "Credit Card"),
            ("Online Payment", "Online Payment"),
        ],
        validators=[DataRequired()],
    )
    cardholder_name = StringField("Cardholder name", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Pay Prescription Charge")
