from datetime import date, timedelta

import pytest

from app import create_app, db
from app.models import Booking, Category, Service, User


@pytest.fixture
def app():
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with test_app.app_context():
        db.drop_all()
        db.create_all()
        category = Category(name="Plumbing", slug="plumbing")
        db.session.add(category)
        db.session.flush()
        db.session.add(
            Service(
                title="Faucet Repair",
                description="Repair leaks and common faucet problems.",
                base_price=89,
                category=category,
            )
        )
        db.session.commit()
    yield test_app
    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def create_user(app, email, role, password="secure-pass-123", name="Test User"):
    with app.app_context():
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def sign_in(client, email, password="secure-pass-123", endpoint="/login"):
    return client.post(
        endpoint,
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_registration_hashes_password_and_assigns_customer_role(client, app):
    response = client.post(
        "/register/customer",
        data={
            "name": "Alex Customer",
            "email": "alex@example.com",
            "phone": "555-0101",
            "password": "secure-pass-123",
            "confirm_password": "secure-pass-123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="alex@example.com").one()
        assert user.role == "customer"
        assert user.password_hash != "secure-pass-123"
        assert user.check_password("secure-pass-123")


def test_provider_registration_login_and_logout(client, app):
    registration = client.post(
        "/register/provider",
        data={
            "name": "Pat Provider",
            "email": "pat@example.com",
            "phone": "555-0123",
            "password": "secure-pass-123",
            "confirm_password": "secure-pass-123",
        },
        follow_redirects=True,
    )
    assert registration.status_code == 200
    assert b"Provider workspace" in registration.data
    with app.app_context():
        provider = User.query.filter_by(email="pat@example.com").one()
        assert provider.role == "provider"
        assert provider.password_hash != "secure-pass-123"

    client.post("/logout")
    login_response = sign_in(client, "pat@example.com")
    assert b"Provider workspace" in login_response.data
    logout_response = client.post("/logout", follow_redirects=True)
    assert logout_response.status_code == 200
    assert b"You have been signed out." in logout_response.data
    assert client.get("/provider/dashboard").status_code == 302


def test_service_search_and_details_are_available(client):
    favicon = client.get("/favicon.ico", follow_redirects=True)
    assert favicon.status_code == 200
    assert favicon.mimetype == "image/svg+xml"
    response = client.get("/services?q=faucet")
    assert response.status_code == 200
    assert b"Faucet Repair" in response.data
    details = client.get("/services/1")
    assert details.status_code == 200
    assert b"Plumbing" in details.data
    assert b"Faucet Repair" in details.data
    assert b"Faucet Repair" in client.get("/services?category=plumbing").data
    assert b"No services match that search" in client.get(
        "/services?q=nonexistent"
    ).data


def test_homepage_and_customer_pages_render(client, app):
    create_user(app, "customer@example.com", "customer")
    assert client.get("/").status_code == 200
    sign_in(client, "customer@example.com")
    assert client.get("/customer/dashboard").status_code == 200
    assert client.get("/customer/services/1/book").status_code == 200
    profile_response = client.post(
        "/customer/profile",
        data={"name": "Alex Updated", "phone": "555-0199"},
        follow_redirects=True,
    )
    assert profile_response.status_code == 200
    assert b"Profile updated." in profile_response.data


def test_customer_can_book_and_review_booking_history(client, app):
    create_user(app, "customer@example.com", "customer")
    sign_in(client, "customer@example.com")
    response = client.post(
        "/customer/services/1/book",
        data={
            "scheduled_for": (date.today() + timedelta(days=2)).isoformat(),
            "address": "123 Main Street, Springfield",
            "notes": "Kitchen faucet is leaking.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Faucet Repair" in response.data
    with app.app_context():
        booking = Booking.query.one()
        assert booking.address == "123 Main Street, Springfield"
        assert booking.scheduled_for == date.today() + timedelta(days=2)


def test_customer_cannot_submit_booking_for_a_past_date(client, app):
    create_user(app, "customer@example.com", "customer")
    sign_in(client, "customer@example.com")
    response = client.post(
        "/customer/services/1/book",
        data={
            "scheduled_for": (date.today() - timedelta(days=1)).isoformat(),
            "address": "123 Main Street, Springfield",
            "notes": "",
        },
    )
    assert response.status_code == 200
    assert b"Choose today or a future date." in response.data
    with app.app_context():
        assert Booking.query.count() == 0


def test_login_returns_to_a_safe_local_booking_url(client, app):
    create_user(app, "customer@example.com", "customer")
    response = client.post(
        "/login?next=/customer/services/1/book",
        data={"email": "customer@example.com", "password": "secure-pass-123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/customer/services/1/book")


def test_login_ignores_external_redirect_targets(client, app):
    create_user(app, "customer@example.com", "customer")
    response = client.post(
        "/login?next=https://example.com/",
        data={"email": "customer@example.com", "password": "secure-pass-123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/customer/dashboard")


def test_provider_dashboard_only_shows_assigned_service_requests(client, app):
    provider_id = create_user(app, "pro@example.com", "provider", name="Pat Provider")
    customer_id = create_user(app, "customer@example.com", "customer")
    with app.app_context():
        service = Service.query.one()
        service.provider_id = provider_id
        db.session.add(
            Booking(
                customer_id=customer_id,
                service_id=service.id,
                scheduled_for=date.today() + timedelta(days=1),
                address="123 Main Street",
            )
        )
        db.session.commit()
    sign_in(client, "pro@example.com")
    response = client.get("/provider/dashboard")
    assert response.status_code == 200
    assert b"Pat Provider" in response.data
    assert b"123 Main Street" in response.data
    assert b"approve" not in response.data.lower()


def test_admin_can_create_service_and_customer_cannot_access_admin(client, app):
    admin_id = create_user(app, "admin@example.com", "admin")
    customer_id = create_user(app, "customer@example.com", "customer")
    sign_in(client, "admin@example.com", endpoint="/admin/login")
    response = client.post(
        "/admin/services/new",
        data={
            "title": "Drain Clearing",
            "category_id": "1",
            "description": "Clear a slow or blocked household drain.",
            "base_price": "95.00",
            "provider_id": "0",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Service.query.filter_by(title="Drain Clearing").one()

    client.post("/logout")
    sign_in(client, "customer@example.com")
    forbidden_redirect = client.get("/admin/")
    assert forbidden_redirect.status_code == 302


def test_admin_can_edit_delete_and_assign_services(client, app):
    provider_id = create_user(
        app, "provider@example.com", "provider", name="Service Provider"
    )
    create_user(app, "admin@example.com", "admin")
    with app.app_context():
        service = Service.query.one()
        service_id = service.id

    sign_in(client, "admin@example.com", endpoint="/admin/login")
    edit_response = client.post(
        f"/admin/services/{service_id}/edit",
        data={
            "title": "Updated Faucet Repair",
            "category_id": "1",
            "description": "Repair leaks and common faucet problems with care.",
            "base_price": "105.00",
            "provider_id": str(provider_id),
        },
        follow_redirects=True,
    )
    assert edit_response.status_code == 200
    with app.app_context():
        updated = db.session.get(Service, service_id)
        assert updated.title == "Updated Faucet Repair"
        assert updated.provider_id == provider_id

    delete_response = client.post(
        f"/admin/services/{service_id}/delete", follow_redirects=True
    )
    assert delete_response.status_code == 200
    with app.app_context():
        assert db.session.get(Service, service_id) is None


def test_admin_login_rejects_non_admin_accounts(client, app):
    create_user(app, "customer@example.com", "customer")
    response = sign_in(client, "customer@example.com", endpoint="/admin/login")
    assert b"Admin email or password is incorrect." in response.data


def test_admin_login_page_preserves_existing_provider_session(client, app):
    create_user(app, "provider@example.com", "provider")
    sign_in(client, "provider@example.com")

    response = client.get("/admin/login")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/provider/dashboard")
    assert client.get("/provider/dashboard").status_code == 200


def test_role_protection_covers_customer_and_provider_dashboards(client, app):
    create_user(app, "customer@example.com", "customer")
    create_user(app, "provider@example.com", "provider")

    assert client.get("/customer/dashboard").status_code == 302
    assert client.get("/provider/dashboard").status_code == 302

    sign_in(client, "provider@example.com")
    assert client.get("/customer/dashboard", follow_redirects=True).request.path == "/"

    client.post("/logout")
    sign_in(client, "customer@example.com")
    assert client.get("/provider/dashboard", follow_redirects=True).request.path == "/"
