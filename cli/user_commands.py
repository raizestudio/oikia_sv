import sys
from pathlib import Path

import typer
from tortoise import Tortoise, run_async
from tortoise.exceptions import IntegrityError

sys.path.append(str(Path(__file__).resolve().parent.parent))

import signals.users
from config import Settings
from models.geo import Email
from models.users import User
from utils.crypt import hash_password

app = typer.Typer()
settings = Settings()


@app.command()
def createuser(username: str, password: str, email: str, first_name: str, last_name: str, is_admin: bool = False, is_superuser: bool = False):
    """Create user"""

    async def _create_user():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={
                "models": [
                    "models.users",
                    "models.auth",
                    "models.clients",
                    "models.geo",
                ]
            },
        )
        password_hash = hash_password(password)
        try:    
            _email = await Email.create(email=email)
            _user = await User.create(
                username=username,
                password=password_hash,
                email=_email,
                first_name=first_name,
                last_name=last_name,
                is_admin=is_admin,
                is_superuser=is_superuser,
            )
            typer.echo(_user)

        except IntegrityError:
            typer.echo(f"User {username} already exists.")

        await Tortoise.close_connections()

    run_async(_create_user())


@app.command()
def listusers():
    """List all users."""

    async def _list_users():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.users"]},
        )
        users = await User.all()
        for user in users:
            typer.echo(user.username)

        await Tortoise.close_connections()

    run_async(_list_users())


if __name__ == "__main__":
    app()
