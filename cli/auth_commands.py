import sys
from pathlib import Path

import typer
from rich import print as r_print
from tortoise import Tortoise, run_async
from tortoise.exceptions import DoesNotExist

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Settings
from models.auth import Permission, Refresh, Session, Token
from models.geo import Email
from models.users import User
from utils.crypt import (
    check_password,
    decode_token,
    generate_refresh_token,
    generate_token,
)

app = typer.Typer()
settings = Settings()


@app.command()
def authenticate(email: str, password: str):
    """Authenticate user"""

    async def _authenticate():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={
                "models": [
                    "models.users",
                    "models.auth",
                    "models.geo",
                    "models.assets",
                    # "models.services",
                    "models.operators",
                ]
            },
        )

        try:
            _email = await Email.get(email=email)
            _user = await User.get(email=_email)

            if not check_password(password, _user.password):
                r_print(f"[bold red]Password[/bold red] [italic white]{password}[/italic white] [bold red]does not match![/bold red] :boom:")

                return

            try:
                _session = await Session.get(user=_user).prefetch_related("token", "refresh")

                generated_token = generate_token(email)
                generated_refresh_token = generate_refresh_token()

                _token = await Token.create(token=generated_token, user=_user)
                _refresh = await Refresh.create(token=generated_refresh_token, user=_user)

                _session.token = _token
                _session.refresh = _refresh
                await _session.save()

                r_print(f"[bold]Generated jwt token[/bold] [bold gray]->[/bold gray] [blue]{generated_token}[/blue]")
                r_print(f"[bold]Generated refresh token[/bold] [bold gray]->[/bold gray] [blue]{generated_refresh_token}[/blue]")
                r_print(f"[bold]Updated session [/bold] [bold gray]->[/bold gray] [blue]{_session}[/blue]")

            except DoesNotExist:
                generated_token = generate_token(email)
                generated_refresh_token = generate_refresh_token()

                _token = await Token.create(token=generated_token, user=_user)
                _refresh = await Refresh.create(token=generated_refresh_token, user=_user)
                _session = await Session.create(token=_token, refresh=_refresh, user=_user)

                r_print(f"[bold]Generated jwt token[/bold] [bold gray]->[/bold gray] [blue]{generated_token}[/blue]")
                r_print(f"[bold]Generated refresh token[/bold] [bold gray]->[/bold gray] [blue]{generated_refresh_token}[/blue]")
                r_print(f"[bold]Generated session [/bold] [bold gray]->[/bold gray] [blue]{_session}[/blue]")

        except DoesNotExist:
            r_print(f"[bold red]User[/bold red] [italic white]{email}[/italic white] [bold red]match does not exist![/bold red] :boom:")

        await Tortoise.close_connections()

    run_async(_authenticate())


@app.command()
def authenticatetoken(token: str, refresh: str):
    """
    Authenticate user using provided token.

    :param token: The jwt token.

    """

    async def _authenticate_token():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.users", "models.auth"]},
        )
        decoded_result = decode_token(token=token)

        if "email" in decoded_result:
            _user = await User.get(email=decoded_result["email"])
            _session = await Session.get(user=_user)

            r_print(f"Session {_session} is valid, the user [italic]{_user}[/italic] is autheticated.")

        elif "error" in decoded_result:
            if decoded_result["error"] == "expired":
                try:
                    _refresh = await Refresh.get(token=refresh).prefetch_related("user")
                    _session = await Session.get(refresh=_refresh)

                    if _refresh.is_valid():
                        generated_token = generate_token(user_email=_refresh.user.email)
                        _token = await Token.create(token=generated_token, user=_refresh.user)

                        _session.token = _token
                        await _session.save()

                        r_print(f"[bold]Generated jwt token[/bold] [bold gray]->[/bold gray] [blue]{generated_token}[/blue]")
                        r_print(f"[bold]Generated session [/bold] [bold gray]->[/bold gray] [blue]{_session}[/blue]")

                except DoesNotExist:
                    pass

        await Tortoise.close_connections()

    run_async(_authenticate_token())


# @app.command()
# def listusers():
#     """List all users."""

#     async def _list_users():
#         await Tortoise.init(
#             db_url=settings.db_url,
#             modules={"models": ["models.users"]},
#         )
#         users = await User.all()
#         for user in users:
#             typer.echo(user.username)

#         await Tortoise.close_connections()

#     run_async(_list_users())


@app.command()
def createpermission(name: str):
    """Create a permission."""

    async def _create_permission():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        permission = await Permission.create(name=name)
        r_print(permission)

        await Tortoise.close_connections()

    run_async(_create_permission())


@app.command()
def listpermissions():
    """List all permissions."""

    async def _list_permissions():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        permissions = await Permission.all()
        for permission in permissions:
            r_print(permission)

        await Tortoise.close_connections()

    run_async(_list_permissions())


@app.command()
def getpermission(name: str):
    """Get permission information"""

    async def _get_permission():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )

        try:
            permission = await Permission.get(name=name)
            r_print(permission)

        except DoesNotExist:
            r_print(f"[bold red]Permission[/bold red] [italic white]{name}[/italic white] [bold red]match does not exist![/bold red] :boom:")

        await Tortoise.close_connections()

    run_async(_get_permission())


if __name__ == "__main__":
    app()
