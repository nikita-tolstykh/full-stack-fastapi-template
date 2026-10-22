from app.core.permissions import ROLE_PERMISSIONS, Role


def test_every_role_has_a_permission_set() -> None:
    assert set(ROLE_PERMISSIONS) == set(Role)
