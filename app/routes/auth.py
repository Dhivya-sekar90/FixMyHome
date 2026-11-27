from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func
from urllib.parse import urlsplit

from app import db
from app.forms import LoginForm, RegistrationForm
from app.models import User

auth_bp = Blueprint("auth", __name__)


def _dashboard_for(user):
    if user.role == "admin":
        return url_for("admin.dashboard")
    if user.role == "provider":
        return url_for("provider.dashboard")
    return url_for("customer.dashboard")


def _safe_next_target(default):
    target = request.args.get("next", "")
    parsed = urlsplit(target)
    if (
        target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
        and not parsed.scheme
        and not parsed.netloc
    ):
        return target
    return default


@auth_bp.route("/register/<role>", methods=["GET", "POST"])
def register(role):
    if role not in ("customer", "provider"):
        return "Not found", 404
    if current_user.is_authenticated:
        return redirect(_dashboard_for(current_user))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing = User.query.filter(
            func.lower(User.email) == form.email.data.strip().lower()
        ).first()
        if existing:
            form.email.errors.append("An account with this email already exists.")
        else:
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                phone=form.phone.data.strip() or None if form.phone.data else None,
                role=role,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account is ready.", "success")
            return redirect(_dashboard_for(user))
    return render_template("auth/register.html", form=form, role=role)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_for(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            func.lower(User.email) == form.email.data.strip().lower()
        ).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Welcome back.", "success")
            return redirect(_safe_next_target(_dashboard_for(user)))
        flash("Email or password is incorrect.", "danger")
    return render_template("auth/login.html", form=form, admin_login=False)


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(_dashboard_for(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            func.lower(User.email) == form.email.data.strip().lower(),
            User.role == "admin",
        ).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Administrator signed in.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Admin email or password is incorrect.", "danger")
    return render_template("auth/login.html", form=form, admin_login=True)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.home"))
