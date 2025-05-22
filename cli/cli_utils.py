import importlib
import json
import sys
from pathlib import Path

import pandas as pd
from rich.console import Console
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist

from models.geo import (
    AdministrativeLevelOne,
    AdministrativeLevelTwo,
    City,
    Street,
    StreetType,
)

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Settings

settings = Settings()
console = Console()


def format_fixture_name(string: str) -> str:
    """Format fixture name to match model class name."""
    return string.replace("_", " ").title().replace(" ", "")


async def load_fixture(app: str, model: str, env: str = "prod") -> None:
    """Load fixture data into the database."""
    await Tortoise.init(
        db_url=settings.db_url,
        modules={"models": [f"models.{model}" for model in settings.models]},
    )

    await Tortoise.generate_schemas()

    module = importlib.import_module(f"models.{app}")
    model_class = getattr(module, format_fixture_name(model))

    with open(f"fixtures/{env}/{model}.json", "r") as f:
        data = json.load(f)

        for item in data:
            for field, value in item.items():
                field_info = model_class._meta.fields_map.get(field)
                if field_info and hasattr(field_info, "related_model"):
                    related_model = field_info.related_model
                    try:
                        related_instance = await related_model.get(**{field_info.to_field: value})
                    except DoesNotExist:
                        related_instance = await related_model.create(**{field_info.to_field: value})
                    item[field] = related_instance

            await model_class.update_or_create(**item)

    await Tortoise.close_connections()


async def load_administrative_levels():
    # TODO:
    # Source URL l2: https://www.data.gouv.fr/fr/datasets/departements-de-france/
    # Source URL l1: https://www.data.gouv.fr/fr/datasets/regions-de-france/
    raise NotImplementedError("Loading administrative levels is not implemented yet.")


async def load_cities():
    """Load cities from a CSV file into the database."""
    # Source URL: https://www.data.gouv.fr/fr/datasets/communes-france-1/
    csv_path = settings.csv_path / "france" / "cities" / "communes-france-2025.csv"

    # --- 1. Pre-load Administrative Level Data ---
    console.print("[cyan]Loading administrative levels into memory...[/cyan]")
    try:
        level_one_db = await AdministrativeLevelOne.all()
        level_one_map = {str(lvl.code_insee): lvl for lvl in level_one_db}

        level_two_db = await AdministrativeLevelTwo.all()
        level_two_map = {str(lvl.code): lvl for lvl in level_two_db}

        console.print(f"[green]Loaded {len(level_one_map)} administrative level one entries.[/green]")
        console.print(f"[green]Loaded {len(level_two_map)} administrative level two entries.[/green]")
    except Exception as e:
        console.print(f"[red]Error loading administrative levels: {e}. Aborting city loading.[/red]")
        return

    # --- 2. Read and Prepare City Data from CSV ---
    console.print(f"[cyan]Reading city data from: {csv_path}...[/cyan]")
    try:
        df = pd.read_csv(
            csv_path,
            sep=",",
            encoding="utf-8",
            dtype={"code_postal": str, "code_insee": str, "reg_code": str, "dep_code": str},
        )

        df = df.rename(
            columns={
                "nom_standard": "name",
                "reg_code": "admin_level_one_csv_code",
                "dep_code": "admin_level_two_csv_code",
            }
        )

        required_csv_cols = ["code_insee", "name", "code_postal", "admin_level_one_csv_code", "admin_level_two_csv_code"]
        missing_cols = [col for col in required_csv_cols if col not in df.columns]
        if missing_cols:
            console.print(f"[red]Error: CSV file {csv_path.name} is missing required columns: {', '.join(missing_cols)}.[/red]")
            return
        df = df[required_csv_cols]

        df.dropna(subset=["code_insee", "name", "code_postal"], inplace=True)
        for col in required_csv_cols:
            if col in df:
                df[col] = df[col].astype(str).str.strip()

        df = df[df["code_insee"] != ""]

        df.drop_duplicates(subset=["code_insee"], keep="first", inplace=True)

    except FileNotFoundError:
        console.print(f"[red]Error: Cities CSV file not found at {csv_path}.[/red]")
        return
    except Exception as e:
        console.print(f"[red]Error reading or parsing cities CSV {csv_path.name}: {e}[/red]")
        return

    if df.empty:
        console.print(f"[yellow]No valid city data found in {csv_path.name} after cleaning and deduplication.[/yellow]")
        return

    city_objects_to_create = []
    for row_dict in df.to_dict(orient="records"):
        lvl1_code_from_csv = row_dict["admin_level_one_csv_code"]
        lvl2_code_from_csv = row_dict["admin_level_two_csv_code"]

        level_one_instance = level_one_map.get(lvl1_code_from_csv)
        level_two_instance = level_two_map.get(lvl2_code_from_csv)

        if not level_one_instance and not level_two_instance:
            # console.print(f"[yellow]Skipping city '{row_dict['name']}' (INSEE: {row_dict['code_insee']}) due to missing both admin levels.[/yellow]")
            continue
        # if not level_one_instance or not level_two_instance:
        #     console.print(f"[yellow]Skipping city '{row_dict['name']}' (INSEE: {row_dict['code_insee']}) due to one or more missing admin levels.[/yellow]")
        #     continue

        city_obj_data = {
            "name": row_dict["name"],
            "code_postal": row_dict["code_postal"],
            "code_insee": row_dict["code_insee"],
            "administrative_level_one": level_one_instance,
            "administrative_level_two": level_two_instance,
        }
        city_objects_to_create.append(City(**city_obj_data))

    if not city_objects_to_create:
        console.print("[yellow]No city objects to create after processing CSV data and admin level mapping.[/yellow]")
        return

    # --- 3. Bulk Create Cities in Database ---
    console.print(f"[cyan]Attempting to bulk create {len(city_objects_to_create)} cities...[/cyan]")
    try:
        await City.bulk_create(city_objects_to_create, ignore_conflicts=True)
        console.print(f"[green]Cities bulk processing complete. {len(city_objects_to_create)} candidates processed.[/green]")
    except Exception as e:
        console.print(f"[red]Error during bulk city creation: {e}[/red]")


async def load_street_types():
    """Load street types from a CSV file into the database."""
    # Source URL: https://www.data.gouv.fr/fr/datasets/finess-types-de-voies/
    csv_path = settings.csv_path / "france" / "streets" / "types" / "interhop-adresses-types-voies.csv"

    # --- 1. Read and Prepare Data from CSV ---
    console.print(f"[cyan]Reading street types from: {csv_path}...[/cyan]")
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8", dtype={"code": str})

        required_cols = ["code", "label"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            console.print(f"[red]Error: CSV file {csv_path.name} is missing required columns: {', '.join(missing_cols)}.[/red]")
            return

        df = df[required_cols]
        df.dropna(subset=required_cols, inplace=True)
        df["code"] = df["code"].astype(str).str.strip()
        df["label"] = df["label"].astype(str).str.strip()

        df = df[df["code"] != ""]
        df = df[df["label"] != ""]

        df.drop_duplicates(subset=["code"], keep="first", inplace=True)

    except FileNotFoundError:
        console.print(f"[red]Error: Street types CSV file not found at {csv_path}.[/red]")
        return
    except Exception as e:
        console.print(f"[red]Error reading or parsing street types CSV {csv_path.name}: {e}[/red]")
        return

    if df.empty:
        console.print(f"[yellow]No valid street types found in {csv_path.name} after cleaning.[/yellow]")
        return

    street_type_objects_to_create = [StreetType(code=row["code"], name=row["label"]) for _, row in df.iterrows()]

    if not street_type_objects_to_create:
        console.print("[yellow]No street type objects to create after processing CSV data.[/yellow]")
        return

    # --- 2. Bulk Create Street Types in Database ---
    console.print(f"[cyan]Attempting to bulk create {len(street_type_objects_to_create)} street types...[/cyan]")
    try:
        await StreetType.bulk_create(street_type_objects_to_create, ignore_conflicts=True)
        console.print(f"[green]Street types bulk processing complete. {len(street_type_objects_to_create)} candidates processed.[/green]")
    except Exception as e:
        console.print(f"[red]Error during bulk street type creation: {e}[/red]")


async def load_streets():
    """Load streets from CSV files into the database."""
    # Source URL: https://www.lesruesdefrance.com/liste_rue_par_dep_csv.php?p=tele
    csv_paths_root = settings.csv_path / "france" / "streets"
    all_csv_files = list(csv_paths_root.glob("*.csv"))

    if not all_csv_files:
        console.print("[yellow]No CSV files found to process.[/yellow]")
        return

    # --- 1. Pre-load data ---
    console.print("[cyan]Loading all cities into memory...[/cyan]")
    try:
        all_cities_db = await City.all()
        cities_map_by_postal_code = {city.code_postal: city for city in all_cities_db}
        console.print(f"[green]Loaded {len(cities_map_by_postal_code)} cities.[/green]")
    except Exception as e:
        console.print(f"[red]Error loading cities: {e}. Aborting street loading.[/red]")
        return

    # --- Street Type Handling ---
    # TODO: Implement robust street type extraction from 'row["name"]'.
    default_street_type_instance = await StreetType.get_or_none(code="ABE")
    if not default_street_type_instance:
        console.print("[yellow]Warning: Default street type 'ABE' not found. Street type might be null.[/yellow]")

    all_street_objects_to_create = []
    processed_identifiers = set()  # Avoid adding exact duplicate Street objects to the batch

    for csv_path in all_csv_files:
        console.print(f"[cyan]Processing file: {csv_path.name}...[/cyan]")
        try:
            df = pd.read_csv(
                csv_path,
                sep=";",
                encoding="utf-8",
                dtype={"CODE_POSTAL": str},
            )
        except Exception as e:
            console.print(f"[red]Error reading or parsing CSV {csv_path.name}: {e}[/red]")
            continue

        df = df.rename(columns={"DEP": "administrative_level_two", "CODECOM": "code_com", "CODEVOIE": "code_path", "LIBVOIE": "name", "LIBCOM": "name_city"})

        required_pandas_cols = ["name", "CODE_POSTAL"]
        optional_pandas_cols = ["code_path", "administrative_level_two", "code_com", "name_city"]

        # Ensure essential columns are present
        missing_cols = [col for col in required_pandas_cols if col not in df.columns]
        if missing_cols:
            console.print(f"[red]Skipping {csv_path.name}, missing required columns: {', '.join(missing_cols)}.[/red]")
            continue

        for row_dict in df.to_dict(orient="records"):
            postal_code = row_dict.get("CODE_POSTAL")
            street_name = row_dict.get("name")

            if not street_name or pd.isna(street_name):
                # console.print(f"[yellow]Skipping row due to empty street name in {csv_path.name}.[/yellow]")
                continue
            street_name = str(street_name).strip()

            city_instance = cities_map_by_postal_code.get(postal_code)
            if not city_instance:
                # console.print(f"[yellow]Skipping street '{street_name}' (Postal: {postal_code}) due to missing city. File: {csv_path.name}[/yellow]")
                continue

            # --- Street Type Logic Placeholder ---
            current_street_type = default_street_type_instance

            street_identifier = (street_name, city_instance.id)
            if street_identifier in processed_identifiers:
                continue
            processed_identifiers.add(street_identifier)

            street_obj_data = {
                "name": street_name,
                "street_type": current_street_type,
                "city": city_instance,
            }
            all_street_objects_to_create.append(Street(**street_obj_data))

        console.print(f"[blue]Collected {len(df)} potential streets from {csv_path.name}. Total candidates: {len(all_street_objects_to_create)}[/blue]")

    if not all_street_objects_to_create:
        console.print("[yellow]No valid street data collected from CSV files to create.[/yellow]")
        return

    # --- 3. Bulk create streets ---
    console.print(f"[cyan]Attempting to bulk create/update {len(all_street_objects_to_create)} streets...[/cyan]")
    try:
        await Street.bulk_create(all_street_objects_to_create, ignore_conflicts=True)
        # Note: `ignore_conflicts=True` doesn't usually return which objects were created vs. ignored.
        console.print(f"[green]Street bulk processing completed. {len(all_street_objects_to_create)} candidates processed.[/green]")
        # TODO: Add logic to check which streets were actually created vs. ignored.
    except Exception as e:
        console.print(f"[red]Error during bulk street creation: {e}[/red]")
        console.print("[yellow]Some streets may not have been created. Consider retrying or individual processing for failed items.[/yellow]")
