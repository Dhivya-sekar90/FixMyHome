# FixMyHome – Home Service Booking Platform

Phase 1 Flask application for customers to discover home services and submit booking requests, providers to view assigned services and requests, and administrators to manage service listings.

## Phase 1 scope

- Customer and provider registration and login with hashed passwords.
- Admin login using credentials created by the seed command.
- Public service categories, search, listing, and details.
- Customer dashboard, profile editing, booking requests, and booking history.
- Provider dashboard showing assigned service listings and their customer requests.
- Admin dashboard and service create/edit/delete management, including provider assignment.
- SQLite persistence, role checks, CSRF protection, and responsive Bootstrap-based pages.

Booking requests collect a preferred date, service address, and optional note. They do not include provider approval, booking status transitions, availability calendars, or other Phase 2 workflow features.

## Requirements

- Python 3.10+
- pip

## Setup

From the project directory, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Set a unique secret key and admin credentials before seeding. Replace the examples with private values:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:FIXMYHOME_ADMIN_EMAIL = "admin@example.com"
$env:FIXMYHOME_ADMIN_PASSWORD = "replace-with-a-strong-password"
$env:FIXMYHOME_ADMIN_NAME = "Site Administrator"
python seed.py
```

The seed command creates the six service categories, one starter listing per category, and the admin account. It is safe to run again; existing categories and starter listings are not duplicated. Set `DATABASE_URL` to use a different SQLAlchemy database URI; the default SQLite database is stored under Flask's `instance` directory.

## Run

Keep the environment variables set in the same PowerShell session, then run:

```powershell
python run.py
```

Open the local address printed by Flask. Customer registration is available from the homepage. Providers can register at `/register/provider`; administrator login is at `/admin/login`.

## Tests

```powershell
python -m pytest
```

Tests use a temporary in-memory SQLite database and do not modify the development database.
