"""Role-based access control tests for MediQueue.

These tests verify that Patient, Doctor, Nurse and Practice Admin accounts can
reach only the pages/API dashboards intended for their role.
"""

import pytest


def login(client, account):
    """Authenticate a seeded test account through the real MediQueue API."""
    response = client.post(
        "/api/login",
        json={
            "email": account["email"],
            "password": account["password"],
            "remember": False,
        },
    )
    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    return response


@pytest.mark.parametrize(
    "protected_url",
    [
        "/patient/dashboard",
        "/staff/dashboard",
        "/admin/dashboard",
    ],
)
def test_unauthenticated_dashboard_pages_redirect_to_login(client, protected_url):
    """Logged-out users must be redirected to the MediQueue login page."""
    response = client.get(protected_url, follow_redirects=False)

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


@pytest.mark.parametrize(
    ("role_name", "allowed_url"),
    [
        ("Patient", "/patient/dashboard"),
        ("Doctor", "/staff/dashboard"),
        ("Nurse", "/staff/dashboard"),
        ("Practice Admin", "/admin/dashboard"),
    ],
)
def test_each_role_can_open_its_own_dashboard(
    client,
    make_role_user,
    role_name,
    allowed_url,
):
    """Each supported MediQueue role can reach its intended dashboard."""
    account = make_role_user(role_name)
    login(client, account)

    response = client.get(allowed_url)

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("role_name", "forbidden_url"),
    [
        ("Patient", "/staff/dashboard"),
        ("Patient", "/admin/dashboard"),
        ("Doctor", "/patient/dashboard"),
        ("Doctor", "/admin/dashboard"),
        ("Nurse", "/patient/dashboard"),
        ("Nurse", "/admin/dashboard"),
        ("Practice Admin", "/patient/dashboard"),
        ("Practice Admin", "/staff/dashboard"),
    ],
)
def test_cross_role_dashboard_access_is_forbidden(
    client,
    make_role_user,
    role_name,
    forbidden_url,
):
    """Authenticated users must not open another role's server-rendered dashboard."""
    account = make_role_user(role_name)
    login(client, account)

    response = client.get(forbidden_url)

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("role_name", "expected_status"),
    [
        ("Doctor", 200),
        ("Nurse", 403),
        ("Patient", 403),
        ("Practice Admin", 403),
    ],
)
def test_only_doctors_can_open_prescription_management(
    client,
    make_role_user,
    role_name,
    expected_status,
):
    """Prescription review/management is a Doctor-only clinical function."""
    account = make_role_user(role_name)
    login(client, account)

    response = client.get("/prescriptions/manage")

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    ("role_name", "expected_status"),
    [
        ("Practice Admin", 200),
        ("Patient", 403),
        ("Doctor", 403),
        ("Nurse", 403),
    ],
)
def test_only_practice_admin_can_open_reports(
    client,
    make_role_user,
    role_name,
    expected_status,
):
    """Administrative reporting must be unavailable to clinical/patient roles."""
    account = make_role_user(role_name)
    login(client, account)

    response = client.get("/reports/")

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    ("role_name", "api_url"),
    [
        ("Patient", "/api/patient/dashboard"),
        ("Doctor", "/api/staff/dashboard"),
        ("Nurse", "/api/staff/dashboard"),
        ("Practice Admin", "/api/admin/dashboard"),
    ],
)
def test_each_role_can_access_its_react_api_dashboard(
    client,
    make_role_user,
    role_name,
    api_url,
):
    """The React-facing API allows each role to load its own dashboard data."""
    account = make_role_user(role_name)
    login(client, account)

    response = client.get(api_url)

    assert response.status_code == 200
    assert response.get_json()["ok"] is True


@pytest.mark.parametrize(
    ("role_name", "api_url", "expected_error"),
    [
        ("Patient", "/api/staff/dashboard", "Staff access required."),
        ("Patient", "/api/admin/dashboard", "Practice admin access required."),
        ("Doctor", "/api/patient/dashboard", "Patient access required."),
        ("Doctor", "/api/admin/dashboard", "Practice admin access required."),
        ("Nurse", "/api/patient/dashboard", "Patient access required."),
        ("Nurse", "/api/admin/dashboard", "Practice admin access required."),
        ("Practice Admin", "/api/patient/dashboard", "Patient access required."),
        ("Practice Admin", "/api/staff/dashboard", "Staff access required."),
    ],
)
def test_cross_role_react_api_dashboard_access_is_forbidden(
    client,
    make_role_user,
    role_name,
    api_url,
    expected_error,
):
    """React API endpoints return an explicit 403 for the wrong authenticated role."""
    account = make_role_user(role_name)
    login(client, account)

    response = client.get(api_url)

    assert response.status_code == 403
    body = response.get_json()
    assert body["ok"] is False
    assert body["error"] == expected_error
