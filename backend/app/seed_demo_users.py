import logging

from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.db import engine
from app.core.permissions import Role
from app.models import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEMO_USERS = {
    "manager@example.com": Role.MANAGER,
    "member@example.com": Role.MEMBER,
}


def seed_demo_users(session: Session) -> None:
    for email, role in DEMO_USERS.items():
        if crud.get_user_by_email(session=session, email=email):
            continue
        user_in = UserCreate(
            email=email,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            full_name=f"Demo {role.value.title()}",
            role=role,
        )
        crud.create_user(session=session, user_create=user_in)
        logger.info("Created demo %s: %s", role.value, email)


def main() -> None:
    if settings.FASTAPI_ENV != "development":
        logger.info("Skipping demo users: they are only seeded in development")
        return
    with Session(engine) as session:
        seed_demo_users(session)


if __name__ == "__main__":
    main()
