from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models import Booking, Service

provider_bp = Blueprint("provider", __name__, url_prefix="/provider")


@provider_bp.before_request
@login_required
def require_provider():
    if current_user.role != "provider":
        flash("This page is available to provider accounts.", "warning")
        return redirect(url_for("main.home"))
    return None


@provider_bp.route("/dashboard")
def dashboard():
    services = Service.query.filter_by(provider_id=current_user.id).order_by(
        Service.title
    ).all()
    bookings = (
        Booking.query.join(Service)
        .filter(Service.provider_id == current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template(
        "provider/dashboard.html", services=services, bookings=bookings
    )
