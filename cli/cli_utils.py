import importlib
import json
import sys
from pathlib import Path

import pandas as pd
from rich.console import Console
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist

from models.geo import (
    Address,
    AdministrativeLevelOne,
    AdministrativeLevelTwo,
    City,
    CityData,
    GeoData,
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


async def load_cities_data():
    """Load cities data from a CSV file into the database."""
    # Source URL: https://www.insee.fr/fr/statistiques/5020062?sommaire=5040030
    # The link above only provides salary for a few cities, not all.
    # It was cleaned and converted to CSV format, data was added.
    csv_path = settings.csv_path / "france" / "analytics" / "salary_per_city.csv"

    # --- 1. Read and Prepare Data from CSV ---
    console.print(f"[cyan]Reading city data from: {csv_path}...[/cyan]")
    try:
        df = pd.read_csv(
            csv_path,
            sep=",",
            encoding="utf-8",
            dtype={"code_postal": str, "p21_pop": str},
        )

        # TODO: Population needs to move, it needs to be per code_insee ( dataset is available, for salary it's not as trivial )
        required_csv_cols = ["code_postal", "salary", "p21_pop"]
        missing_cols = [col for col in required_csv_cols if col not in df.columns]

        if missing_cols:
            console.print(f"[red]Error: CSV file {csv_path.name} is missing required columns: {', '.join(missing_cols)}.[/red]")
            return

        df = df[required_csv_cols]
        df.dropna(subset=["code_postal", "salary", "p21_pop"], inplace=True)
        for col in required_csv_cols:
            if col in df:
                df[col] = df[col].astype(str).str.strip()

        df = df[df["code_postal"] != ""]
        df.drop_duplicates(subset=["code_postal"], keep="first", inplace=True)

    except FileNotFoundError:
        console.print(f"[red]Error: Cities CSV file not found at {csv_path}.[/red]")
        return

    except Exception as e:
        console.print(f"[red]Error reading or parsing cities CSV {csv_path.name}: {e}[/red]")
        return

    if df.empty:
        console.print(f"[yellow]No valid city data found in {csv_path.name} after cleaning and deduplication.[/yellow]")
        return

    city_data_objects_to_create = []
    for row_dict in df.to_dict(orient="records"):
        # city_instance = await City.get_or_none(code_postal=row_dict["code_postal"])
        city_instances = await City.filter(code_postal=row_dict["code_postal"]).prefetch_related("administrative_level_one", "administrative_level_two")

        if not city_instances:
            console.print(f"[yellow]Skipping city data for '{row_dict['code_postal']}' due to missing city instance.[/yellow]")
            continue

        for city_instance in city_instances:
            city_data_obj_data = {
                "city": city_instance,
                "median_income": row_dict["salary"],
                "population": row_dict["p21_pop"],
            }
            city_data_objects_to_create.append(CityData(**city_data_obj_data))

    #     if not city_instance:
    #         console.print(f"[yellow]Skipping city data for '{row_dict['code_postal']}' due to missing city instance.[/yellow]")
    #         continue

    #     city_data_obj_data = {
    #         "city": city_instance,
    #         "salary": row_dict["salary"],
    #     }
    #     city_data_objects_to_create.append(CityData(**city_data_obj_data))

    if not city_data_objects_to_create:
        console.print("[yellow]No city data objects to create after processing CSV data and city instance mapping.[/yellow]")
        return
    # --- 3. Bulk Create City Data in Database ---
    console.print(f"[cyan]Attempting to bulk create {len(city_data_objects_to_create)} city data objects...[/cyan]")
    try:
        await CityData.bulk_create(city_data_objects_to_create, ignore_conflicts=True)
        console.print(f"[green]City data bulk processing complete. {len(city_data_objects_to_create)} candidates processed.[/green]")

    except Exception as e:
        console.print(f"[red]Error during bulk city data creation: {e}[/red]")
        console.print("[yellow]Some city data may not have been created. Consider retrying or individual processing for failed items.[/yellow]")


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


async def load_addresses():
    """Load addresses from CSV files into the database."""
    # todo Source URL:
    csv_paths_root = settings.csv_path / "france" / "addresses"
    all_csv_files = list(csv_paths_root.glob("*.csv.gz"))

    if not all_csv_files:
        console.print("[yellow]No address CSV files found to process.[/yellow]")
        return

    # --- 1. Pre-load data ---
    console.print("[cyan]Loading all streets into memory...[/cyan]")
    try:
        all_streets_db = await Street.all()
        streets_map_by_name = {f"{street.name}": street for street in all_streets_db}
        console.print(f"[green]Loaded {len(streets_map_by_name)} streets.[/green]")
    except Exception as e:
        console.print(f"[red]Error loading streets: {e}. Aborting address loading.[/red]")
        return

    all_address_objects_to_create = []
    processed_identifiers = set()  # Avoid adding exact duplicate Address objects to the batch
    for csv_path in all_csv_files:
        console.print(f"[cyan]Processing file: {csv_path.name}...[/cyan]")
        try:
            df = pd.read_csv(
                csv_path,
                sep=";",
                encoding="utf-8",
                dtype={"code_postal": str, "code_insee": str},
                compression="gzip",
            )
        except Exception as e:
            console.print(f"[red]Error reading or parsing CSV {csv_path.name}: {e}[/red]")
            continue

        # df = df.rename(columns={"code_postal": "code_postal", "code_insee": "insee_code", "voie": "street_name", "numero": "number"})

        required_pandas_cols = ["nom_afnor", "code_postal", "numero"]
        optional_pandas_cols = ["code_insee", "x", "y"]

        # Ensure essential columns are present
        missing_cols = [col for col in required_pandas_cols if col not in df.columns]
        if missing_cols:
            console.print(f"[red]Skipping {csv_path.name}, missing required columns: {', '.join(missing_cols)}.[/red]")
            continue

        for row_dict in df.to_dict(orient="records"):
            street_name = row_dict.get("nom_afnor")
            code_postal = row_dict.get("code_postal")
            number = row_dict.get("numero")
            latitude = row_dict.get("x")
            longitude = row_dict.get("y")

            if not street_name or pd.isna(street_name):
                # console.print(f"[yellow]Skipping row due to empty street name in {csv_path.name}.[/yellow]")
                continue
            street_name = str(street_name).strip()

            if not code_postal or pd.isna(code_postal):
                # console.print(f"[yellow]Skipping row due to empty postal code in {csv_path.name}.[/yellow]")
                continue
            code_postal = str(code_postal).strip()

            street_identifier = f"{street_name} {row_dict.get('street_type', '')}".strip()
            street_instance = streets_map_by_name.get(street_identifier)

            if not street_instance:
                # console.print(f"[yellow]Skipping address '{street_identifier}' (Postal: {postal_code}) due to missing street. File: {csv_path.name}[/yellow]")
                continue

            address_identifier = (street_instance.id, number, code_postal)
            if address_identifier in processed_identifiers:
                continue
            processed_identifiers.add(address_identifier)
            address_obj_data = {
                "street": street_instance,
                "number": number,
                "postal_code": code_postal,
                "latitude": latitude,
                "longitude": longitude,
            }
            if "code_insee" in row_dict and row_dict["code_insee"]:
                address_obj_data["code_insee"] = row_dict["code_insee"]

            all_address_objects_to_create.append(Address(**address_obj_data))

        if not all_address_objects_to_create:
            console.print("[yellow]No valid address data collected from CSV files to create.[/yellow]")
            return

    # --- 2. Bulk create addresses ---
    console.print(f"[cyan]Attempting to bulk create/update {len(all_address_objects_to_create)} addresses...[/cyan]")
    try:
        await Address.bulk_create(all_address_objects_to_create, ignore_conflicts=True)
        # Note: `ignore_conflicts=True` doesn't usually return which objects were created vs. ignored.
        console.print(f"[green]Address bulk processing completed. {len(all_address_objects_to_create)} candidates processed.[/green]")

    except Exception as e:
        console.print(f"[red]Error during bulk address creation: {e}[/red]")
        console.print("[yellow]Some addresses may not have been created. Consider retrying or individual processing for failed items.[/yellow]")


async def read_geojson(file_path: Path) -> dict:
    """Read a GeoJSON file and return its content."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        return geojson_data
    except FileNotFoundError:
        console.print(f"[red]Error: GeoJSON file not found at {file_path}.[/red]")
        return {}
    except json.JSONDecodeError as e:
        console.print(f"[red]Error decoding GeoJSON file {file_path.name}: {e}[/red]")
        return {}
    except Exception as e:
        console.print(f"[red]Unexpected error reading GeoJSON file {file_path.name}: {e}[/red]")
        return {}


async def load_geo_data():
    """Load geo data from GeoJSON files into the database."""
    geojson_path = settings.json_path / "france" / "regions.json"

    console.print(f"[cyan]Loading geo data from: {geojson_path}...[/cyan]")
    geo_data = await read_geojson(geojson_path)

    if not geo_data:
        console.print("[red]No valid geo data found to process.[/red]")
        return

    for feature in geo_data.get("features", []):
        code_insee = feature["properties"].get("code")
        if not code_insee:
            console.print(f"[yellow]Skipping feature without INSEE code: {feature['properties']}[/yellow]")
            continue

        level_one_instance = await AdministrativeLevelOne.get_or_none(code_insee=code_insee)
        if not level_one_instance:
            console.print(f"[yellow]AdministrativeLevelOne with code {code_insee} not found. Creating new instance.[/yellow]")
            level_one_instance = await AdministrativeLevelOne.create(code_insee=code_insee, geojson=feature)

        await GeoData.update_or_create(geojson=feature, administrative_level_one=level_one_instance)

    console.print("[green]Geo data loaded successfully.[/green]")
