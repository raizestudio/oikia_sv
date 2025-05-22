import sys
from pathlib import Path

import pandas as pd
import typer
from cli_utils import load_communes, load_fixture
from rich import print as r_print
from rich.console import Console
from rich.table import Table
from tortoise import Tortoise, run_async
from tortoise.exceptions import DoesNotExist

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Settings
from models.auth import Permission
from models.core import Menu
from models.geo import Continent

app = typer.Typer()
settings = Settings()
console = Console()

CSVS = [
    "communes-france-2025",
]

FIXTURES = [
    "geo.language",
    "geo.currency",
    "geo.continent",
    "geo.country",
    "geo.country_data",
    "geo.administrative_level_one",
    "geo.administrative_level_two",
    # "geo.city_type",
    # "geo.city",
    "geo.street_type",
    # "geo.street",
    # "geo.address",
    "geo.top_level_domain",
    "assets.asset_type",
    # "assets.asset",
    # "services.service_type",
    # "services.service",
]


@app.command()
def createmenu(name: str):
    """Create menu"""

    async def _create_menu():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.core"]},
        )
        _menu = await Menu.create(name=name)
        typer.echo(_menu)

        await Tortoise.close_connections()

    run_async(_create_menu())


@app.command()
def listmenus():
    """List all menus."""

    async def _list_menu():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.core"]},
        )
        _menus = await Menu.all()
        for menu in _menus:
            typer.echo(menu.name)

        await Tortoise.close_connections()

    run_async(_list_menu())


@app.command()
def getmenu(name: str):
    """Get menu information"""

    async def _get_menu():
        await Tortoise.init(db_url=settings.db_url, modules={"models": ["models.core"]})

        try:
            _menu = await Menu.get(name=name)
            table = Table("ID", "NAME", "PARENT")
            table.add_row(str(_menu.id), _menu.name, _menu.parent)
            console.print(table)

        except DoesNotExist:
            r_print(f"[bold red]Menu[/bold red] [italic white]{name}[/italic white] [bold red]match does not exist![/bold red] :boom:")

        await Tortoise.close_connections()

    run_async(_get_menu())


@app.command()
def resetdb():
    """Reset database"""

    async def _reset_db():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        await Menu.all().delete()
        await Continent.all().delete()

        await Tortoise.close_connections()

    run_async(_reset_db())


@app.command()
def loadfixture(app: str, model: str, env: str = typer.Argument("prod")):
    """Load fixture data"""

    async def _load_fixture():
        await load_fixture(app, model, env)

    run_async(_load_fixture())


@app.command()
def loadallfixtures(env: str = typer.Argument("prod")):
    """
    Load all fixture data

    Args:
        env: The environment to load the fixtures.
    """

    async def _load_all_fixtures():
        for fixture in FIXTURES:
            print(f"Loading fixture: {fixture}")
            app, model = fixture.split(".")
            await load_fixture(app, model, env)

    run_async(_load_all_fixtures())


@app.command()
def generateallpermissions():
    """Generate all permissions"""

    async def _generate_all_permissions():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        models = [
            # AGENCY
            "agency",
            # ASSETS
            "asset",
            # AUTH
            "token",
            "refresh",
            "api_key",
            "session",
            # "permission",
            # CLIENTS
            "client",
            # CORE
            "menu",
            # FINANCIAL
            "tax",
            "simulation",
            "order",
            # GEO
            "language",
            "currency",
            "calling_code",
            "phone_number",
            "top_level_domain",
            "email",
            "continent",
            "country",
            "country_data",
            "administrative_level_one",
            "administrative_level_two",
            # "city_type",
            "city",
            "street_type",
            "street",
            "address",
            # OPERATORS
            "operator",
            # SERVICES
            "service",
            # USERS
            "user",
            "user_preferences",
            "user_security",
            "profile",
        ]
        permissions = [
            "create",
            "read",
            "update",
            "delete",
        ]

        def combine_permissions(models, permissions):
            return [f"{model}:{permission}" for model in models for permission in permissions]

        for permission in combine_permissions(models, permissions):
            await Permission.get_or_create(name=permission)

        await Tortoise.close_connections()

    run_async(_generate_all_permissions())


@app.command()
def loaddatasets():
    """Load datasets from CSV files into the database."""

    async def _load_datasets():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        console.print("[bold cyan]Loading datasets...[/bold cyan]")

        for dataset_name in CSVS:
            csv_path = settings.csv_path / "france" / f"{dataset_name}.csv"
            print(csv_path)
            if not csv_path.exists():
                console.print(f"[yellow]Skipping {dataset_name} (CSV not found).[/yellow]")
                continue

            console.print(f"[blue]Processing:[/blue] {dataset_name}")

            if dataset_name == "communes-france-2025":
                await load_communes(csv_path)

            # elif dataset_name == "departments-france":
            #     await load_departments(csv_path)

            # Add other dataset-specific loaders here...

        await Tortoise.close_connections()
        console.print("[green]✅ All datasets loaded successfully.[/green]")

    run_async(_load_datasets())


if __name__ == "__main__":
    app()
