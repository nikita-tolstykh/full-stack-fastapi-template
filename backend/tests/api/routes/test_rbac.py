import logging
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.permissions import Role
from tests.utils.item import create_random_item
from tests.utils.user import authentication_headers_for_role, create_random_user
from tests.utils.utils import random_email, random_lower_string

API = settings.API_V1_STR
Headers = dict[str, str]


def expect(*, admin: int, manager: int, member: int) -> list[Any]:
    return [
        pytest.param(role, status, id=f"{role}-{status}")
        for role, status in (
            (Role.ADMIN, admin),
            (Role.MANAGER, manager),
            (Role.MEMBER, member),
        )
    ]


@pytest.fixture(scope="module")
def headers_by_role(client: TestClient, db: Session) -> dict[Role, Headers]:
    return {
        role: authentication_headers_for_role(client=client, db=db, role=role)
        for role in Role
    }


def own_user_id(client: TestClient, headers: Headers) -> str:
    return str(client.get(f"{API}/users/me", headers=headers).json()["id"])


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=200, member=403)
)
def test_list_users(
    client: TestClient,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    r = client.get(f"{API}/users/", headers=headers_by_role[role])
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=200, member=403)
)
def test_read_another_user(
    client: TestClient,
    db: Session,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    other = create_random_user(db)
    r = client.get(f"{API}/users/{other.id}", headers=headers_by_role[role])
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=403, member=403)
)
def test_create_user(
    client: TestClient,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    data = {"email": random_email(), "password": random_lower_string()}
    r = client.post(f"{API}/users/", headers=headers_by_role[role], json=data)
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=403, member=403)
)
def test_update_another_user(
    client: TestClient,
    db: Session,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    other = create_random_user(db)
    r = client.patch(
        f"{API}/users/{other.id}",
        headers=headers_by_role[role],
        json={"full_name": "Renamed"},
    )
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=403, member=403)
)
def test_delete_another_user(
    client: TestClient,
    db: Session,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    other = create_random_user(db)
    r = client.delete(f"{API}/users/{other.id}", headers=headers_by_role[role])
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=200, member=403)
)
def test_read_metrics(
    client: TestClient,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    r = client.get(f"{API}/metrics/", headers=headers_by_role[role])
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=403, member=403)
)
def test_read_another_users_item(
    client: TestClient,
    db: Session,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    item = create_random_item(db)
    r = client.get(f"{API}/items/{item.id}", headers=headers_by_role[role])
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=201, manager=403, member=403)
)
def test_send_test_email(
    client: TestClient,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    with patch("app.api.routes.utils.send_email"):
        r = client.post(
            f"{API}/utils/test-email/",
            headers=headers_by_role[role],
            params={"email_to": random_email()},
        )
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"), expect(admin=200, manager=200, member=200)
)
def test_update_own_profile(
    client: TestClient,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_status: int,
) -> None:
    r = client.patch(
        f"{API}/users/me",
        headers=headers_by_role[role],
        json={"full_name": f"Own {role} profile"},
    )
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_permissions"),
    [
        (
            Role.ADMIN,
            [
                "items:manage_all",
                "metrics:read",
                "settings:manage",
                "users:create",
                "users:manage",
                "users:read",
            ],
        ),
        (Role.MANAGER, ["metrics:read", "users:read"]),
        (Role.MEMBER, []),
    ],
)
def test_me_returns_role_permissions(
    client: TestClient,
    headers_by_role: dict[Role, Headers],
    role: Role,
    expected_permissions: list[str],
) -> None:
    r = client.get(f"{API}/users/me", headers=headers_by_role[role])
    assert r.status_code == 200
    assert r.json()["role"] == role
    assert r.json()["permissions"] == expected_permissions


def test_member_cannot_change_own_role_via_profile(
    client: TestClient, headers_by_role: dict[Role, Headers]
) -> None:
    headers = headers_by_role[Role.MEMBER]
    r = client.patch(f"{API}/users/me", headers=headers, json={"role": "admin"})
    assert r.status_code == 200
    assert client.get(f"{API}/users/me", headers=headers).json()["role"] == "member"


def test_signup_ignores_requested_role(client: TestClient) -> None:
    data = {"email": random_email(), "password": random_lower_string()}
    r = client.post(f"{API}/users/signup", json={**data, "role": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "member"


def test_manager_cannot_promote_themselves(
    client: TestClient, headers_by_role: dict[Role, Headers]
) -> None:
    headers = headers_by_role[Role.MANAGER]
    user_id = own_user_id(client, headers)
    r = client.patch(f"{API}/users/{user_id}", headers=headers, json={"role": "admin"})
    assert r.status_code == 403


def test_admin_cannot_change_own_role(
    client: TestClient, headers_by_role: dict[Role, Headers]
) -> None:
    headers = headers_by_role[Role.ADMIN]
    user_id = own_user_id(client, headers)
    r = client.patch(f"{API}/users/{user_id}", headers=headers, json={"role": "member"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Users are not allowed to change their own role"


def test_admin_can_change_another_users_role(
    client: TestClient, db: Session, headers_by_role: dict[Role, Headers]
) -> None:
    other = create_random_user(db)
    r = client.patch(
        f"{API}/users/{other.id}",
        headers=headers_by_role[Role.ADMIN],
        json={"role": "manager"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "manager"


def test_missing_token_is_unauthorized(client: TestClient) -> None:
    r = client.get(f"{API}/users/me")
    assert r.status_code == 401


def test_invalid_token_is_unauthorized(client: TestClient) -> None:
    r = client.get(f"{API}/users/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_denied_request_is_logged(
    client: TestClient,
    headers_by_role: dict[Role, Headers],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.api.deps"):
        client.get(f"{API}/users/", headers=headers_by_role[Role.MEMBER])
    assert "Permission denied" in caplog.text
    assert "permission=users:read" in caplog.text
