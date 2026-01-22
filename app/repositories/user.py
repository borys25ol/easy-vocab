from sqlmodel import Session, select

from app.models.user import User


class UserRepository:
    """Data access for User entities."""

    def get_by_username(self, session: Session, username: str) -> User | None:
        """Fetch a user by username."""
        statement = select(User).where(User.username == username)
        return session.exec(statement).first()
