import importlib
import json
import sys
from pathlib import Path

from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist

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
