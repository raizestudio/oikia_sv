import json
from enum import IntEnum

from httpx import AsyncClient
from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet

from utils.cache import get_from_cache, set_in_cache


class AdministrativeLevelsEnum(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2


class AnalyticsMixin:
    """Provides logic for auto-calculating population density."""

    async def calculate_density(self):
        if getattr(self, "population", None) is not None and getattr(self, "area", None) not in (None, 0):
            self.population_density = self.population / self.area
        else:
            self.population_density = None

    async def save(self, *args, **kwargs):
        await self.calculate_density()
        await super().save(*args, **kwargs)


class Language(Model):
    """Model for languages."""

    code = fields.CharField(primary_key=True, max_length=4, unique=True)
    name = fields.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.code


class Currency(Model):
    """Model for currencies."""

    code = fields.CharField(primary_key=True, max_length=3, unique=True)
    code_numeric = fields.CharField(max_length=3, unique=True)
    name = fields.CharField(max_length=50, unique=True)
    symbol = fields.CharField(max_length=5, null=True)
    minor_unit = fields.IntField()

    def __str__(self):
        return self.code


class CallingCode(Model):
    """Model for phone calling codes."""

    code = fields.CharField(primary_key=True, max_length=5, unique=True)

    country = fields.ForeignKeyField("models.Country", related_name="country_calling_code")

    def __str__(self):
        return self.code


class PhoneNumber(Model):
    """Model for phone numbers."""

    phone_number = fields.CharField(max_length=32, unique=True)

    calling_code = fields.ForeignKeyField("models.CallingCode", related_name="calling_code")

    class Meta:
        unique_together = ("phone_number", "calling_code")


class TopLevelDomain(Model):
    """Model for top-level domains."""

    code = fields.CharField(primary_key=True, max_length=5, unique=True)
    operator = fields.CharField(max_length=50, null=True)
    idn = fields.BooleanField(default=False)
    dnssec = fields.BooleanField(default=False)
    sld = fields.BooleanField(default=False)
    ipv6 = fields.BooleanField(default=False)

    country = fields.ForeignKeyField("models.Country", related_name="country_top_level_domain", null=True)

    def __str__(self):
        return self.domain


class Email(Model):
    """Model for emails."""

    email = fields.CharField(primary_key=True, max_length=255, unique=True)

    def __str__(self):
        return self.email


class Continent(Model):
    """Model for continents."""

    code = fields.CharField(primary_key=True, max_length=2, unique=True)
    name = fields.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Country(Model):
    """Model for countries."""

    code_iso2 = fields.CharField(primary_key=True, max_length=2, unique=True)
    code_iso3 = fields.CharField(max_length=3, unique=True)
    onu_code = fields.CharField(max_length=3, unique=True)
    name = fields.CharField(max_length=100, unique=True)

    language_official = fields.ForeignKeyField("models.Language", related_name="official_language")
    language_others = fields.ManyToManyField("models.Language", related_name="other_languages")
    currency = fields.ForeignKeyField("models.Currency", related_name="currency")
    continent = fields.ForeignKeyField("models.Continent", related_name="continent")

    def __str__(self):
        return self.name


class CountryData(Model):
    """Model for country data."""

    population = fields.IntField(null=True)
    area = fields.FloatField(null=True)
    population_density = fields.FloatField(null=True)
    gdp = fields.FloatField(null=True)
    gdp_per_capita = fields.FloatField(null=True)
    inflation = fields.FloatField(null=True)
    human_development_index = fields.FloatField(null=True)
    administrative_levels = fields.IntEnumField(
        enum_type=AdministrativeLevelsEnum,
        choices=AdministrativeLevelsEnum,
        default=AdministrativeLevelsEnum.ZERO,
    )
    administrative_level_one_label = fields.CharField(max_length=50, null=True)
    administrative_level_two_label = fields.CharField(max_length=50, null=True)

    country = fields.OneToOneField("models.Country", related_name="country_data_country")

    def calculate_population_density(self):
        if self.area and self.population:
            return self.population / self.area
        return None

    def calculate_gdp_per_capita(self):
        if self.gdp and self.population:
            return self.gdp / self.population
        return None

    def __str__(self):
        return self.country.name


class AdministrativeLevelOne(Model):
    """Model for administrative level one."""

    code = fields.CharField(primary_key=True, max_length=8, unique=True)
    name = fields.CharField(max_length=50, unique=True)
    code_insee = fields.CharField(max_length=10, null=True)  # INSEE code for France, might be null or different entity for other countries

    country = fields.ForeignKeyField("models.Country", related_name="administrative_level_one_country")

    def __str__(self):
        return self.name


class AdministrativeLevelTwo(Model):
    """Model for administrative level two."""

    code = fields.CharField(primary_key=True, max_length=8, unique=True)
    numeric_code = fields.IntField(null=True)
    name = fields.CharField(max_length=50, unique=True)

    administrative_level_one = fields.ForeignKeyField(
        "models.AdministrativeLevelOne",
        related_name="administrative_level_two_administrative_level_one",
    )

    def __str__(self):
        return self.name

    # class CityType(Model):
    # """Model for city types."""

    # code = fields.CharField(primary_key=True, max_length=10)
    # name = fields.CharField(max_length=32)
    # description = fields.TextField(null=True)
    # population_min = fields.IntField(null=True)
    # population_max = fields.IntField(null=True)

    # def __str__(self):
    # return self.code


class City(Model):
    """Model for cities."""

    name = fields.CharField(max_length=50)
    code_postal = fields.CharField(max_length=10, null=True)
    code_insee = fields.CharField(max_length=10, null=True)

    administrative_level_one = fields.ForeignKeyField(
        "models.AdministrativeLevelOne",
        related_name="administrative_level_one",
        null=True,
    )
    administrative_level_two = fields.ForeignKeyField(
        "models.AdministrativeLevelTwo",
        related_name="administrative_level_two",
        null=True,
    )

    class Meta:
        unique_together = ("name", "administrative_level_one", "administrative_level_two")
        # indexes = [
        #     ("name", "administrative_level_one"),
        #     ("name", "administrative_level_two"),
        # ]

    def __str__(self):
        return self.name


class CityData(AnalyticsMixin, Model):
    """Model for city statistics."""

    population = fields.IntField(null=True)
    area = fields.FloatField(null=True)
    population_density = fields.FloatField(null=True)
    median_income = fields.FloatField(null=True)

    city = fields.OneToOneField("models.City", related_name="city_data_city")


class StreetType(Model):

    code = fields.CharField(primary_key=True, max_length=10, unique=True)
    name = fields.CharField(max_length=50)
    short_name = fields.CharField(max_length=10, null=True)

    def __str__(self):
        return self.name


class Street(Model):
    """Model for streets."""

    name = fields.CharField(max_length=50)

    street_type = fields.ForeignKeyField("models.StreetType", related_name="street_type")
    city = fields.ForeignKeyField("models.City", related_name="city")

    class Meta:
        unique_together = ("name", "street_type", "city")
        ordering = ["id"]
        # ordering = ("city__name", "name", "street_type__code")
        indexes = [
            ("name", "street_type", "city"),
            ("name", "city"),
        ]
        # indexes = [
        #     ("name", "street_type"),
        #     ("name", "city"),
        # ]

    def __str__(self):
        return self.name


class Address(Model):
    """Model for addresses."""

    number = fields.CharField(max_length=10)
    number_extension = fields.CharField(max_length=10, null=True)
    complement = fields.CharField(max_length=50, null=True)
    latitude = fields.FloatField(null=True)
    longitude = fields.FloatField(null=True)

    street = fields.ForeignKeyField("models.Street", related_name="street", null=True)

    @classmethod
    async def api_gov_adresse_connector(cls, api_gov_feature: dict):
        """
        Translate API Adresse Feature in to Address.

        Args:
            api_gov_address (dict): A Feature from the API Adresse.

        Returns:
            dict: The address data.
        """
        if api_gov_feature:
            _type = api_gov_feature.get("type")
            geometry = api_gov_feature.get("geometry")
            properties = api_gov_feature.get("properties")
            _address = (
                await cls.filter(number=properties.get("housenumber"), street__name=properties.get("street"), street__city__name=properties.get("city"))
                .first()
                .prefetch_related("street", "street__city")
            )
            print(f"Address: {_address}")
            if _address:
                return _address
            else:
                # TODO: Handle the case where the address does not exist.
                ...

        # return address_data

    @classmethod
    async def search_address_gov(cls, address: str):
        """
        Search an address using the API Adresse from data.gouv.fr.

        Args:
            address (str): The address to search.

        Returns:
            dict: The response from the API.
            bool: True if the response is from the cache, False otherwise.
        """
        response = None
        is_cached = False

        cached_response = get_from_cache(address)
        if cached_response:
            cached_response = cached_response.decode("utf-8")

            response = json.loads(cached_response)
            is_cached = True

        else:
            async with AsyncClient() as client:
                api_response = await client.get(f"https://api-adresse.data.gouv.fr/search/?q={address}&limit=5")
                if api_response.status_code != 200:
                    return None

                json_response = api_response.json()
                set_in_cache(address, json.dumps(json_response), 600)
                response = json_response

        return response, is_cached

    def __str__(self):
        return f"{self.number} {self.street}"


class GeoData(Model):
    """Model for geographical data."""

    geojson = fields.JSONField(null=True)

    continent = fields.ForeignKeyField("models.Continent", related_name="geo_data_continent", null=True)
    country = fields.ForeignKeyField("models.Country", related_name="geo_data_country", null=True)
    administrative_level_one = fields.ForeignKeyField("models.AdministrativeLevelOne", related_name="geo_data_administrative_level_one", null=True)
    administrative_level_two = fields.ForeignKeyField("models.AdministrativeLevelTwo", related_name="geo_data_administrative_level_two", null=True)
    city = fields.ForeignKeyField("models.City", related_name="geo_data_city", null=True)
    street = fields.ForeignKeyField("models.Street", related_name="geo_data_street", null=True)

    def validate_single_fk(self):
        """Validate that exactly one foreign key is set."""
        fks = [
            self.continent_id,
            self.country_id,
            self.administrative_level_one_id,
            self.administrative_level_two_id,
            self.city_id,
            self.street_id,
        ]
        if sum(1 for x in fks if x is not None) != 1:
            raise ValueError("GeoData must be linked to exactly one entity.")

    @property
    def linked_entity_type(self):
        for field in [
            "continent",
            "country",
            "administrative_level_one",
            "administrative_level_two",
            "city",
            "street",
        ]:
            if getattr(self, f"{field}_id") is not None:
                return field
        return None

    async def save(self, *args, **kwargs):
        """Override save method to validate single foreign key."""
        self.validate_single_fk()
        await super().save(*args, **kwargs)
