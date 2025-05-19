import sys
from pathlib import Path

import typer
from rich import print as r_print
from rich.console import Console
from rich.table import Table
from tortoise import Tortoise, run_async
from tortoise.exceptions import DoesNotExist

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Settings
from models.geo import Continent, Country, Currency, Language

app = typer.Typer()
settings = Settings()
console = Console()


@app.command()
def listcontinents():
    """List all continents."""

    async def _list_continents():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _continents = await Continent.all()
        table = Table("Code", "Name")
        for continent in _continents:
            table.add_row(continent.code, continent.name)
        console.print(table)

        await Tortoise.close_connections()

    run_async(_list_continents())


@app.command()
def createcontinent(code: str, name: str):
    """Create continent"""

    async def _create_continent():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _continent = await Continent.create(code=code, name=name)
        typer.echo(_continent)

        await Tortoise.close_connections()

    run_async(_create_continent())


@app.command()
def getcontinent(code: str):
    """Get continent"""

    async def _get_continent():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        try:
            _continent = await Continent.get(code=code)
            table = Table("Code", "Name")
            table.add_row(_continent.code, _continent.name)
            console.print(table)

        except DoesNotExist:
            typer.echo(f"Continent with code {code} does not exist.")

        await Tortoise.close_connections()

    run_async(_get_continent())


@app.command()
def createcurrency(
    code: str,
    code_numeric: str,
    name: str,
    minor_unit: int = typer.Option(2, help="Minor unit of the currency"),
):
    """
    Create currency

    Args:
        code (str): Currency code
        code_numeric (str): Currency code numeric
        name (str): Currency name
        minor_unit (int, optional): Minor unit of the currency. Defaults to 2.
    """

    async def _create_currency():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _currency = await Currency.create(code=code, code_numeric=code_numeric, name=name, minor_unit=minor_unit)
        typer.echo(_currency)

        await Tortoise.close_connections()

    run_async(_create_currency())


@app.command()
def listcurrencies():
    """List all currencies."""

    async def _list_currencies():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _currencies = await Currency.all()
        table = Table("Code", "Code numeric", "Name", "Minor Unit")
        for currency in _currencies:
            table.add_row(
                currency.code,
                currency.code_numeric,
                currency.name,
                str(currency.minor_unit),
            )
        console.print(table)

        await Tortoise.close_connections()

    run_async(_list_currencies())


@app.command()
def getcurrency(code: str):
    """Get currency"""

    async def _get_currency():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        try:
            _currency = await Currency.get(code=code)
            table = Table("Code", "Code numeric", "Name", "Minor Unit")
            table.add_row(
                _currency.code,
                _currency.code_numeric,
                _currency.name,
                str(_currency.minor_unit),
            )
            console.print(table)

        except DoesNotExist:
            typer.echo(f"Currency with code {code} does not exist.")

        await Tortoise.close_connections()

    run_async(_get_currency())


@app.command()
def listlanguages():
    """List all languages."""

    async def _list_languages():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _languages = await Language.all()
        table = Table("Code", "Name")
        for language in _languages:
            table.add_row(language.code, language.name)
        console.print(table)

        await Tortoise.close_connections()

    run_async(_list_languages())


@app.command()
def createlanguage(code: str, name: str):
    """Create language"""

    async def _create_language():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _language = await Language.create(code=code, name=name)
        typer.echo(_language)

        await Tortoise.close_connections()

    run_async(_create_language())


@app.command()
def getlanguage(code: str):
    """Get language"""

    async def _get_language():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        try:
            _language = await Language.get(code=code)
            table = Table("Code", "Name")
            table.add_row(_language.code, _language.name)
            console.print(table)

        except DoesNotExist:
            typer.echo(f"Language with code {code} does not exist.")

        await Tortoise.close_connections()

    run_async(_get_language())


@app.command()
def listcountries():
    """List all countries."""

    async def _list_countries():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _countries = await Country.all()
        table = Table("Code Iso 2", "Code Iso 3")
        for country in _countries:
            table.add_row(country.code_iso2, country.code_iso3)
        console.print(table)

        await Tortoise.close_connections()

    run_async(_list_countries())


@app.command()
def createcountry(
    code_iso2: str,
    code_iso3: str,
    onu_code: str,
    name: str,
    language: str,
    continent: str,
    currency: str,
):
    """
    Create country

    Args:
        code_iso2 (str): Country code ISO 2
        code_iso3 (str): Country code ISO 3
        onu_code (str): Country ONU code
        name (str): Country name
        language (str): Language code
        continent (str): Continent code
        currency (str): Currency code
    """

    async def _create_country():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        _language = await Language.get(code=language)
        _continent = await Continent.get(code=continent)
        _currency = await Currency.get(code=currency)
        _country = await Country.create(
            code_iso2=code_iso2,
            code_iso3=code_iso3,
            onu_code=onu_code,
            name=name,
            language_official=_language,
            continent=_continent,
            currency=_currency,
        )
        typer.echo(_country)

        await Tortoise.close_connections()

    run_async(_create_country())


@app.command()
def getcountry(code_iso2: str):
    """Get country"""

    async def _get_country():
        await Tortoise.init(
            db_url=settings.db_url,
            modules={"models": ["models.geo"]},
        )
        try:
            _country = await Country.get(code_iso2=code_iso2).prefetch_related("continent", "currency", "language_official")
            table = Table(
                "Code Iso 2",
                "Code Iso 3",
                "ONU Code",
                "Name",
                "Language Officiel",
                "Continent",
                "Currency",
            )
            table.add_row(
                _country.code_iso2,
                _country.code_iso3,
                _country.onu_code,
                _country.name,
                _country.language_official.name,
                _country.continent.name,
                _country.currency.name,
            )
            console.print(table)

        except DoesNotExist:
            typer.echo(f"Country with code ISO 2 {code_iso2} does not exist.")

        await Tortoise.close_connections()

    run_async(_get_country())


if __name__ == "__main__":
    app()
