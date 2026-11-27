from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import ServiceForm
from app.models import Booking, Category, Service, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
def require_admin():
    if current_user.role != "admin":
        flash("Administrator access is required.", "warning")
        return redirect(url_for("main.home"))
    return None


def _populate_service_form(form):
    form.category_id.choices = [
        (category.id, category.name) for category in Category.query.order_by(Category.name)
    ]
    form.provider_id.choices = [(0, "Not assigned")] + [
        (provider.id, provider.name)
        for provider in User.query.filter_by(role="provider").order_by(User.name)
    ]


@admin_bp.route("/")
def dashboard():
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template(
        "admin/dashboard.html",
        services=services,
        service_count=Service.query.count(),
        customer_count=User.query.filter_by(role="customer").count(),
        provider_count=User.query.filter_by(role="provider").count(),
        booking_count=Booking.query.count(),
    )


@admin_bp.route("/services/new", methods=["GET", "POST"])
def create_service():
    form = ServiceForm()
    _populate_service_form(form)
    if form.validate_on_submit():
        service = Service(
            title=form.title.data.strip(),
            category_id=form.category_id.data,
            description=form.description.data.strip(),
            base_price=form.base_price.data,
            provider_id=form.provider_id.data or None,
        )
        db.session.add(service)
        db.session.commit()
        flash("Service created.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/service_form.html", form=form, heading="Add a service")


@admin_bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
def edit_service(service_id):
    service = db.get_or_404(Service, service_id)
    form = ServiceForm(obj=service)
    _populate_service_form(form)
    if not form.is_submitted():
        form.provider_id.data = service.provider_id or 0
    if form.validate_on_submit():
        service.title = form.title.data.strip()
        service.category_id = form.category_id.data
        service.description = form.description.data.strip()
        service.base_price = form.base_price.data
        service.provider_id = form.provider_id.data or None
        db.session.commit()
        flash("Service updated.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template(
        "admin/service_form.html", form=form, heading="Edit service"
    )


@admin_bp.route("/services/<int:service_id>/delete", methods=["POST"])
def delete_service(service_id):
    service = db.get_or_404(Service, service_id)
    if service.bookings:
        flash("This service has booking history and cannot be deleted.", "warning")
        return redirect(url_for("admin.dashboard"))
    db.session.delete(service)
    db.session.commit()
    flash("Service deleted.", "success")
    return redirect(url_for("admin.dashboard"))
