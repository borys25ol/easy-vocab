from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.core.config import settings
from app.models.user import User


class UserRepository:
    """Data access for User entities."""

    def get_by_username(self, session: Session, username: str) -> User | None:
        """Fetch a user by username."""
        statement = select(User).where(User.username == username)
        return session.exec(statement).first()

    def bump_token_version(self, session: Session, user: User) -> User:
        """Revoke every token already issued to this user."""
        user.token_version += 1
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def record_failed_login(self, session: Session, user: User) -> User:
        """Count a failed attempt and lock the account once it hits the limit."""
        user.failed_login_count += 1
        if user.failed_login_count >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(UTC) + timedelta(
                minutes=settings.LOGIN_LOCKOUT_MINUTES
            )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def clear_failed_logins(self, session: Session, user: User) -> User:
        """Reset the throttle after a successful sign in."""
        if user.failed_login_count == 0 and user.locked_until is None:
            return user

        user.failed_login_count = 0
        user.locked_until = None
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
