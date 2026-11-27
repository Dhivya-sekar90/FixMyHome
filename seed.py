import os
import sys

from sqlalchemy import func

from app import create_app, db
from app.models import Category, Service, User

CATEGORIES = [
    ("Plumbing", "plumbing"),
    ("Electrical", "electrical"),
    ("AC Repair", "ac-repair"),
    ("Cleaning", "cleaning"),
    ("Carpentry", "carpentry"),
    ("Painting", "painting"),
]

STARTER_SERVICES = [
    ("Faucet and Pipe Repair", "plumbing", "Repair common faucet leaks, pipe drips, and everyday plumbing issues.", 89),
    ("Home Electrical Repair", "electrical", "Get help troubleshooting switches, outlets, and common household electrical issues.", 99),
    ("Air Conditioner Service", "ac-repair", "Routine inspection and repair for common residential air conditioning problems.", 119),
    ("Standard Home Cleaning", "cleaning", "A thorough clean for the main living areas, kitchen, and bathrooms in your home.", 99),
    ("Furniture and Fixture Repair", "carpentry", "Help with minor woodwork, furniture repairs, and household fixtures.", 79),
    ("Interior Room Painting", "painting", "Refresh an interior room with careful preparation and a professional finish.", 199),
]


def seed():
    admin_email = os.environ.get("FIXMYHOME_ADMIN_EMAIL", "").strip().lower()
    admin_password = os.environ.get("FIXMYHOME_ADMIN_PASSWORD", "")
    admin_name = os.environ.get("FIXMYHOME_ADMIN_NAME", "FixMyHome Admin").strip()
    if not admin_email or len(admin_password) < 8:
        raise ValueError(
            "Set FIXMYHOME_ADMIN_EMAIL and FIXMYHOME_ADMIN_PASSWORD "
            "(at least 8 characters) before running seed.py."
        )

    app = create_app()
    with app.app_context():
        category_by_slug = {}
        for name, slug in CATEGORIES:
            category = Category.query.filter_by(slug=slug).first()
            if category is None:
                category = Category(name=name, slug=slug)
                db.session.add(category)
            category_by_slug[slug] = category
        db.session.flush()

        for title, slug, description, price in STARTER_SERVICES:
            exists = Service.query.filter(
                func.lower(Service.title) == title.lower()
            ).first()
            if exists is None:
                db.session.add(
                    Service(
                        title=title,
                        category=category_by_slug[slug],
                        description=description,
                        base_price=price,
                    )
                )

        admin = User.query.filter(
            func.lower(User.email) == admin_email
        ).first()
        if admin is None:
            admin = User(name=admin_name, email=admin_email, role="admin")
            admin.set_password(admin_password)
            db.session.add(admin)
        elif admin.role != "admin":
            raise ValueError("The configured admin email belongs to a non-admin account.")

        db.session.commit()
        print("Seeded six service categories, starter services, and the admin account.")


if __name__ == "__main__":
    try:
        seed()
    except ValueError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
