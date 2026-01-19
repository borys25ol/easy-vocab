import argparse
import sys

from sqlmodel import Session, select

from app.core.database import create_db_and_tables, engine
from app.core.security import get_password_hash
from app.models.user import User


def create_user(username: str, password: str) -> None:
    create_db_and_tables()
    with Session(engine) as session:
        # Check if user already exists
        statement = select(User).where(User.username == username)
        existing_user = session.exec(statement).first()
        if existing_user:
            print(f"Error: User '{username}' already exists.")
            sys.exit(1)

        hashed_password = get_password_hash(password)
        user = User(username=username, hashed_password=hashed_password)
        session.add(user)
        session.commit()
        print(f"Success: User '{username}' created.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Application Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # create-user command
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_user_parser.add_argument(
        "--username", required=True, help="Username for the new user"
    )
    create_user_parser.add_argument(
        "--password", required=True, help="Password for the new user"
    )

    args = parser.parse_args()

    if args.command == "create-user":
        create_user(args.username, args.password)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
