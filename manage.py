import secrets
import sys

import click
from sqlmodel import select

from app.core.database import create_db_and_tables, get_session
from app.core.security import get_password_hash
from app.models.user import User


@click.group()
def cli() -> None:
    """Application management CLI."""


def generate_mcp_api_key() -> str:
    """Generate a random MCP API key for a user."""
    return secrets.token_urlsafe(32)


def create_user(username: str, password: str) -> None:
    """Create a new user and print the generated MCP API key."""
    create_db_and_tables()
    with next(get_session()) as session:
        statement = select(User).where(User.username == username)
        existing_user = session.exec(statement).first()
        if existing_user:
            click.echo(f"Error: User '{username}' already exists.")
            sys.exit(1)

        hashed_password = get_password_hash(password)
        mcp_api_key = generate_mcp_api_key()
        user = User(
            username=username,
            hashed_password=hashed_password,
            mcp_api_key=mcp_api_key,
        )
        session.add(user)
        session.commit()
        click.echo(f"Success: User '{username}' created.")
        click.echo(f"MCP API Key: {mcp_api_key}")


def rotate_mcp_key(username: str) -> None:
    """Rotate the MCP API key for an existing user."""
    create_db_and_tables()
    with next(get_session()) as session:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        if not user:
            click.echo(f"Error: User '{username}' not found.")
            sys.exit(1)

        mcp_api_key = generate_mcp_api_key()
        user.mcp_api_key = mcp_api_key
        session.add(user)
        session.commit()
        click.echo(f"Success: MCP API key rotated for '{username}'.")
        click.echo(f"MCP API Key: {mcp_api_key}")


def backfill_mcp_keys() -> None:
    """Generate MCP API keys for users missing one."""
    create_db_and_tables()
    with next(get_session()) as session:
        statement = select(User).where(User.mcp_api_key.is_(None))  # type: ignore
        users = session.exec(statement).all()
        if not users:
            click.echo("No users missing MCP API keys.")
            return

        for user in users:
            user.mcp_api_key = generate_mcp_api_key()
            session.add(user)
        session.commit()
        click.echo(f"Backfilled MCP API keys for {len(users)} user(s).")


@cli.command("create-user")
@click.option("--username", required=True, help="Username for the new user")
@click.option("--password", required=True, help="Password for the new user")
def create_user_command(username: str, password: str) -> None:
    """Create a new user."""
    create_user(username, password)


@cli.command("rotate-mcp-key")
@click.option("--username", required=True, help="Username to rotate MCP API key")
def rotate_mcp_key_command(username: str) -> None:
    """Rotate MCP API key for a user."""
    rotate_mcp_key(username)


@cli.command("backfill-mcp-keys")
def backfill_mcp_keys_command() -> None:
    """Generate MCP API keys for users missing one."""
    backfill_mcp_keys()


if __name__ == "__main__":
    cli()
