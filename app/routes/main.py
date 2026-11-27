from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy import or_

from app import db
from app.models import Category, Service

main_bp = Blueprint("main", __name__)


@main_bp.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="images/favicon.svg"))


@main_bp.route("/")
def home():
    categories = Category.query.order_by(Category.name).all()
    services = Service.query.order_by(Service.created_at.desc()).limit(6).all()
    return render_template("home.html", categories=categories, services=services)


@main_bp.route("/services")
def services():
    term = request.args.get("q", "").strip()
    category_slug = request.args.get("category", "").strip()
    query = Service.query.join(Category)
    if term:
        like = f"%{term}%"
        query = query.filter(
            or_(Service.title.ilike(like), Service.description.ilike(like))
        )
    if category_slug:
        query = query.filter(Category.slug == category_slug)
    results = query.order_by(Service.title).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "services.html",
        services=results,
        categories=categories,
        search_term=term,
        selected_category=category_slug,
    )


@main_bp.route("/services/<int:service_id>")
def service_detail(service_id):
    service = db.get_or_404(Service, service_id)
    return render_template("service_detail.html", service=service)
