import typer
from auth_commands import app as auth_app
from core_commands import app as core_app
from geo_commands import app as geo_app
from user_commands import app as user_app

app = typer.Typer()

app.add_typer(core_app, name="core")
app.add_typer(auth_app, name="auth")
app.add_typer(user_app, name="user")
app.add_typer(geo_app, name="geo")

if __name__ == "__main__":
    app()
