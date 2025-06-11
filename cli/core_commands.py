import asyncio
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
import typer
from bs4 import BeautifulSoup
from cli_utils import (
    load_addresses,
    load_cities,
    load_cities_data,
    load_fixture,
    load_geo_data,
    load_street_types,
    load_streets,
)
from rich import print as r_print
from rich.console import Console
from rich.table import Table
from tortoise import Tortoise, run_async
from tortoise.exceptions import DoesNotExist

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Settings
from models.auth import Permission
from models.core import Menu
from models.geo import AdministrativeLevelOne, Continent, Country, GeoData

app = typer.Typer()
settings = Settings()
console = Console()
from typing import List

CSVS = [
    "communes-france-2025",
]

FIXTURES = [
    "core.menu",
    "geo.language",
    "geo.currency",
    "geo.continent",
    "geo.country",
    "geo.country_data",
    "geo.administrative_level_one",
    "geo.administrative_level_two",
    # "geo.city_type",
    # "geo.city",
    # "geo.street_type",
    # "geo.street",
    # "geo.address",
    "geo.top_level_domain",
    "assets.asset_type",
    # "assets.asset",
    # "services.service_type",
    # "services.service",
]


@app.command()
def createmenu(
    name: str,
    path: str = typer.Option(None, help="URL path for the menu item"),
    icon: str = typer.Option(None, help="Icon for the menu item"),
    description: str = typer.Option(None, help="Optional description of the menu"),
    parent: int = typer.Option(None, help="ID of the parent menu, if any"),
):
    """Create menu"""

    async def _create_menu():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.core"]},
        )
        _parent = await Menu.get_or_none(id=parent) if parent else None
        if parent and not _parent:
            r_print(f"[bold red]Parent menu[/bold red] [italic white]{parent}[/italic white] [bold red]does not exist![/bold red] :boom:")
            raise typer.Exit(code=1)

        _menu = await Menu.create(name=name, path=path, icon=icon, description=description, parent=_parent)
        console.print(f"[bold green]Menu[/bold green] [italic white]{_menu.name}[/italic white] [bold green]created successfully![/bold green] :tada:")

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
def loaddev(flags: List[str] = []):
    if not flags:
        # No flags: run everything by default
        loadallfixtures("dev")
        loaddatasets()
        loadgeodata()
        return

    if "fixtures" in flags:
        loadallfixtures("dev")
    if "datasets" in flags:
        loaddatasets()
    if "geodata" in flags:
        loadgeodata()


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
def fetchdatasets():
    """Fetch datasets from the web and store them in proper directories."""

    async def _fetch_datasets():
        # TODO: Just very basic implementation, need to be improved ( e.g. handle multiple sources )
        # Source URL: https://adresse.data.gouv.fr/data/ban/adresses/latest/csv
        console.print("[bold cyan]Fetching datasets...[/bold cyan]")
        base_url = "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv"
        try:
            response = requests.get(base_url)
            response.raise_for_status()
        except requests.RequestException as e:
            console.print(f"[bold red]Error fetching datasets:[/bold red] {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        links = []

        for a_tag in soup.find_all("a"):
            href = a_tag.get("href")
            if href and href.endswith(".csv.gz"):
                abs_url = urljoin(base_url, href)
                links.append(abs_url)

        if not links:
            console.print("[bold red]No CSV files found.[/bold red]")
            return

        for link in links:
            filename = link.split("/")[-1]
            filepath = Path(settings.csv_path) / "france" / "addresses" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            if not filepath.exists():
                try:
                    r = requests.get(link, stream=True)
                    r.raise_for_status()
                    with open(filepath, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    console.print(f"[green]Downloaded:[/green] {filename}")
                except requests.RequestException as e:
                    console.print(f"[bold red]Error downloading {filename}:[/bold red] {e}")
            else:
                console.print(f"[yellow]File already exists:[/yellow] {filename}")

    asyncio.run(_fetch_datasets())


@app.command()
def loaddatasets():
    """Load datasets from CSV files into the database."""

    async def _load_datasets():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        console.print("[bold cyan]Loading datasets...[/bold cyan]")

        console.print(f"[blue]Processing:[/blue] cities.")
        await load_cities()

        console.print(f"[blue]Processing:[/blue] cities data.")
        await load_cities_data()

        console.print(f"[blue]Processing:[/blue] street types.")
        await load_street_types()

        console.print(f"[blue]Processing:[/blue] streets.")
        await load_streets()

        console.print(f"[blue]Processing:[/blue] addresses.")
        await load_addresses()

        await Tortoise.close_connections()
        console.print("[green]✅ All datasets loaded successfully.[/green]")

    run_async(_load_datasets())


@app.command()
def loadgeodata():
    """Load geographical data from the web and store it in the database."""

    async def _load_geo_data():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        console.print("[bold cyan]Loading geographical data...[/bold cyan]")

        console.print(f"[blue]Processing:[/blue] France regions.")
        await load_geo_data()

    run_async(_load_geo_data())


@app.command()
def test():
    """Just for testing purposes"""

    async def _test():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
        )
        console.print("[blue]Processing:[/blue] test command.")

        await load_addresses()
        console.print("[bold green]Testing command was successful![/bold green]")

    run_async(_test())


if __name__ == "__main__":
    app()
