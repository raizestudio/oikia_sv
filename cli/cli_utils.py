import importlib
import json
import sys
from pathlib import Path

import pandas as pd
from rich.console import Console
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist

from models.geo import AdministrativeLevelOne, AdministrativeLevelTwo, City

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Settings

settings = Settings()


def format_fixture_name(string: str) -> str:
    return string.replace("_", " ").title().replace(" ", "")


async def load_fixture(app: str, model: str, env: str = "prod") -> None:
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


async def load_communes(csv_path: Path):
    df = pd.read_csv(csv_path, sep=",", encoding="utf-8", dtype={"code_postal": str, "code_insee": str})

    df = df.rename(columns={"nom_standard": "name", "reg_code": "administrative_level_one", "dep_code": "administrative_level_two"})
    df = df[["code_insee", "name", "code_postal", "administrative_level_one", "administrative_level_two"]]

    level_one_map = {lvl.code_insee: lvl async for lvl in AdministrativeLevelOne.all()}
    level_two_map = {lvl.code: lvl async for lvl in AdministrativeLevelTwo.all()}

    for _, row in df.iterrows():
        lvl1_code = str(row["administrative_level_one"])
        lvl2_code = str(row["administrative_level_two"])

        level_one = level_one_map.get(lvl1_code)
        level_two = level_two_map.get(lvl2_code)

        if not level_one and not level_two:
            console.print(f"[red]Skipping {row['name']} due to missing admin levels.[/red]")
            continue

        await City.get_or_create(
            name=row["name"],
            code_postal=row["code_postal"],
            code_insee=row["code_insee"],
            administrative_level_one=level_one,
            administrative_level_two=level_two,
        )
