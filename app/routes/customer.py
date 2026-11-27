from datetime import date

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import BookingForm, ProfileForm
from app.models import Booking, Service

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


@customer_bp.before_request
@login_required
def require_customer():
    if current_user.role != "customer":
        flash("This page is available to customer accounts.", "warning")
        return redirect(url_for("main.home"))
    return None


@customer_bp.route("/dashboard")
def dashboard():
    bookings = (
        Booking.query.filter_by(customer_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template("customer/dashboard.html", bookings=bookings)


@customer_bp.route("/bookings")
def bookings():
    items = (
        Booking.query.filter_by(customer_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("customer/bookings.html", bookings=items)


@customer_bp.route("/services/<int:service_id>/book", methods=["GET", "POST"])
def book_service(service_id):
    service = db.get_or_404(Service, service_id)
    form = BookingForm()
    if form.validate_on_submit():
        booking = Booking(
            customer_id=current_user.id,
            service_id=service.id,
            scheduled_for=form.scheduled_for.data,
            address=form.address.data.strip(),
            notes=form.notes.data.strip() if form.notes.data else None,
        )
        db.session.add(booking)
        db.session.commit()
        flash("Your booking request has been submitted.", "success")
        return redirect(url_for("customer.bookings"))
    return render_template(
        "customer/book_service.html", service=service, form=form, today=date.today()
    )


@customer_bp.route("/profile", methods=["GET", "POST"])
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.phone = form.phone.data.strip() or None if form.phone.data else None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("customer.profile"))
    return render_template("customer/profile.html", form=form)
