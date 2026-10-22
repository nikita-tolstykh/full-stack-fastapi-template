"""
Role-based access control: the single place that maps roles to permissions.

Routes check permissions, never role names. To add a role, add it to `Role`
and give it a permission set in `ROLE_PERMISSIONS`.
"""

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class Permission(StrEnum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_MANAGE = "users:manage"
    METRICS_READ = "metrics:read"
    ITEMS_MANAGE_ALL = "items:manage_all"
    SETTINGS_MANAGE = "settings:manage"


# Anything every signed-in user can do (own profile, own items) needs no permission.
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.MANAGER: frozenset({Permission.USERS_READ, Permission.METRICS_READ}),
    Role.MEMBER: frozenset(),
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]


def permissions_for(role: Role) -> list[Permission]:
    return sorted(ROLE_PERMISSIONS[role])
