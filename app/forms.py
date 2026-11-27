from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)


class RegistrationForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=30)])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=128)]
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class BookingForm(FlaskForm):
    scheduled_for = DateField(
        "Preferred service date",
        format="%Y-%m-%d",
        validators=[InputRequired()],
    )
    address = StringField(
        "Service address", validators=[DataRequired(), Length(min=5, max=300)]
    )
    notes = TextAreaField(
        "Notes for the provider", validators=[Optional(), Length(max=1000)]
    )
    submit = SubmitField("Request booking")

    def validate_scheduled_for(self, field):
        if field.data and field.data < date.today():
            raise ValidationError("Choose today or a future date.")


class ProfileForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    submit = SubmitField("Save profile")


class ServiceForm(FlaskForm):
    title = StringField("Service title", validators=[DataRequired(), Length(max=120)])
    category_id = SelectField("Category", coerce=int, validators=[InputRequired()])
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(min=10, max=5000)]
    )
    base_price = DecimalField(
        "Starting price ($)",
        places=2,
        validators=[InputRequired(), NumberRange(min=0, max=999999)],
    )
    provider_id = SelectField(
        "Assigned provider (optional)",
        coerce=int,
        validators=[Optional()],
        choices=[(0, "Not assigned")],
    )
    submit = SubmitField("Save service")
