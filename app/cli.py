import typer
from typing import Annotated
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from sqlmodel import select, or_, col
from sqlalchemy.exc import IntegrityError
cli = typer.Typer()



@cli.command()
def initialize():
    """Drop and recreate all database tables, then seed a default user."""
    with get_session() as db:
        drop_all()
        create_db_and_tables()
        bob = User('bob', 'bob@mail.com', 'bobpass')
        db.add(bob)
        db.commit()
        db.refresh(bob)
        print("Database Initialized")

@cli.command()
def get_user(username: Annotated[str, typer.Argument(help="Username of the user to retrieve")]):
    """Retrieve and print a single user by their username."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """Print all users in the database."""
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command()
def change_email(
    username: Annotated[str, typer.Argument(help="Username of the user to update")],
    new_email: Annotated[str, typer.Argument(help="New email address to assign")]
):
    """Update the email address of an existing user."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: Annotated[str, typer.Argument(help="Unique username for the new user")],
    email:    Annotated[str, typer.Argument(help="Unique email for the new user")],
    password: Annotated[str, typer.Argument(help="Password for the new user")]
):
    """Create a new user, handling duplicate username/email gracefully."""
    with get_session() as db:
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError:
            db.rollback()
            print("Username or email already taken!")
        else:
            print(newuser)

@cli.command()
def delete_user(username: Annotated[str, typer.Argument(help="Username of the user to delete")]):
    """Delete a user by their username."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

@cli.command()
def search_users(query: Annotated[str, typer.Argument(help="Partial text to match against username or email")]):
    """Search for users whose username or email contains the given query string."""
    with get_session() as db:
        users = db.exec(
            select(User).where(
                or_(
                    col(User.username).contains(query),
                    col(User.email).contains(query)
                )
            )
        ).all()
        if not users:
            print(f'No users found matching "{query}"')
            return
        for user in users:
            print(user)

@cli.command()
def list_users(
    limit:  Annotated[int, typer.Option(help="Maximum number of users to return")] = 10,
    offset: Annotated[int, typer.Option(help="Number of users to skip before returning results")] = 0
):
    """List users with pagination support using limit and offset."""
    with get_session() as db:
        users = db.exec(select(User).offset(offset).limit(limit)).all()
        if not users:
            print("No users found")
            return
        for user in users:
            print(user)

if __name__ == "__main__":
    cli()