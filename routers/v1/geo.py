from typing import Annotated, List

from fastapi import APIRouter, Query, status

from models.geo import (  # CityType,
    Address,
    AdministrativeLevelOne,
    AdministrativeLevelTwo,
    CallingCode,
    City,
    CityData,
    Continent,
    Country,
    Currency,
    GeoData,
    Language,
    PhoneNumber,
    Street,
    StreetType,
    TopLevelDomain,
)
from schemas.geo import (
    AddressCreate,
    AddressRead,
    AdministrativeLevelOneCreate,
    AdministrativeLevelOneRead,
    AdministrativeLevelTwoCreate,
    AdministrativeLevelTwoRead,
    CallingCodeCreate,
    CityCreate,
    CityRead,
    CityTypeCreate,
    ContinentCreate,
    ContinentRead,
    CountryCreate,
    CountryRead,
    CurrencyCreate,
    LanguageCreate,
    PhoneNumberCreate,
    StreetCreate,
    StreetRead,
    StreetTypeCreate,
    TopLevelDomainCreate,
)
from schemas.pagination import PaginatedResponse

router = APIRouter()


@router.get("/languages")
async def get_languages():
    _languages = await Language.all()
    return _languages


@router.get("/languages/{language}")
async def get_language(language: str):
    _language = await Language.get(code=language)
    return _language


@router.post("/languages")
async def create_language(language: LanguageCreate):
    _language = await Language.create(code=language.code, name=language.name)
    return _language


@router.get("/currencies")
async def get_currencies():
    _currencies = await Currency.all()
    return _currencies


@router.get("/currencies/{currency}")
async def get_currency(currency: str):
    _currency = await Currency.get(code=currency)
    return _currency


@router.post("/currencies")
async def create_currency(currency: CurrencyCreate):
    _currency = await Currency.create(
        code=currency.code,
        code_numeric=currency.code_numeric,
        name=currency.name,
        symbol=currency.symbol,
        minor_unit=currency.minor_unit,
    )
    return _currency


@router.get("/calling-codes")
async def get_calling_codes():
    _calling_codes = await CallingCode.all()
    return _calling_codes


@router.get("/calling-codes/{calling_code}")
async def get_calling_code(calling_code: str):
    _calling_code = await CallingCode.get(code=calling_code)
    return _calling_code


@router.post("/calling-codes")
async def create_calling_code(calling_code: CallingCodeCreate):
    _country = await Country.get(code_iso2=calling_code.country)
    _calling_code = await CallingCode.create(code=calling_code.code, country=_country)
    return _calling_code


@router.get("/phone-numbers")
async def get_phone_numbers():
    _phone_numbers = await PhoneNumber.all()
    return _phone_numbers


@router.get("/phone-numbers/{phone_number}")
async def get_phone_number(phone_number: str):
    _phone_number = await PhoneNumber.get(phone_number=phone_number)
    return _phone_number


@router.post("/phone-numbers")
async def create_phone_number(phone_number: PhoneNumberCreate):
    _calling_code = await CallingCode.get(code=phone_number.calling_code)
    _phone_number = await PhoneNumber.create(phone_number=phone_number.phone_number, calling_code=_calling_code)
    return _phone_number


@router.get("/top-level-domains")
async def get_top_level_domains():
    _top_level_domains = await TopLevelDomain.all()
    return _top_level_domains


@router.get("/top-level-domains/{top_level_domain}")
async def get_top_level_domain(top_level_domain: str):
    _top_level_domain = await TopLevelDomain.get(code=top_level_domain)
    return _top_level_domain


@router.post("/top-level-domains")
async def create_top_level_domain(top_level_domain: TopLevelDomainCreate):
    _country = await Country.get(code_iso2=top_level_domain.country)
    _top_level_domain = await TopLevelDomain.create(
        code=top_level_domain.code,
        operator=top_level_domain.operator,
        idn=top_level_domain.idn,
        dnssec=top_level_domain.dnssec,
        sld=top_level_domain.sld,
        ipv6=top_level_domain.ipv6,
        country=_country,
    )
    return _top_level_domain


@router.get("/continents", response_model=PaginatedResponse[ContinentRead])
async def get_continents(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Retrieve a list of continents."""
    count = await Continent.all().count()
    offset = (page - 1) * size
    _continents = await Continent.all().offset(offset).limit(size).values("code", "name")
    return PaginatedResponse[ContinentRead](
        count=count,
        page=page,
        size=size,
        data=_continents,
    )


@router.post("/continents")
async def create_continent(continent: ContinentCreate):
    _continent = await Continent.create(code=continent.code, name=continent.name)
    return _continent


@router.get("/continents/{continent}")
async def get_continent(continent: str):
    _continent = await Continent.get(code=continent)
    return _continent


@router.get("/countries", response_model=PaginatedResponse[CountryRead], response_model_by_alias=False)
async def get_countries(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    count = await Country.all().count()
    offset = (page - 1) * size

    _countries = (
        await Country.all()
        .offset(offset)
        .limit(size)
        .values(
            "code_iso2",
            "code_iso3",
            "onu_code",
            "name",
            "language_official__code",
            "continent__code",
            "currency__code",
        )
    )

    return PaginatedResponse[CountryRead](
        count=count,
        page=page,
        size=size,
        data=_countries,
    )


@router.get("/countries/{country}")
async def get_country(country: str):
    _country = await Country.get(code_iso2=country)
    return _country


@router.post("/countries")
async def create_country(country: CountryCreate):
    _continent = await Continent.get(code=country.continent)
    _language_official = await Language.get(code=country.language_official)
    _currency = await Currency.get(code=country.currency)
    _country = await Country.create(
        code_iso2=country.code_iso2,
        code_iso3=country.code_iso3,
        onu_code=country.onu_code,
        name=country.name,
        language_official=_language_official,
        continent=_continent,
        currency=_currency,
    )
    return _country


@router.get("/administrative-levels-ones", response_model=PaginatedResponse[AdministrativeLevelOneRead], response_model_by_alias=False)
async def get_administrative_levels_one(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Retrieve a list of administrative levels one."""
    count = await AdministrativeLevelOne.all().count()
    offset = (page - 1) * size
    _administrative_levels_one = await AdministrativeLevelOne.all().offset(offset).limit(size).values("code", "name", "country__code_iso2")
    return PaginatedResponse[AdministrativeLevelOneRead](
        count=count,
        page=page,
        size=size,
        data=_administrative_levels_one,
    )


@router.get("/administrative-levels-one/{administrative_level_one}")
async def get_administrative_level_one(administrative_level_one: str):
    _administrative_level_one = await AdministrativeLevelOne.get(code=administrative_level_one)
    return _administrative_level_one


@router.post("/administrative-levels-one")
async def create_administrative_level_one(
    administrative_level_one: AdministrativeLevelOneCreate,
):
    _country = await Country.get(code_iso2=administrative_level_one.country)
    _administrative_level_one = await AdministrativeLevelOne.create(
        code=administrative_level_one.code,
        name=administrative_level_one.name,
        country=_country,
    )
    return _administrative_level_one


@router.get("/administrative-levels-twos", response_model=PaginatedResponse[AdministrativeLevelTwoRead], response_model_by_alias=False)
async def get_administrative_levels_two(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Retrieve a list of administrative levels two."""
    count = await AdministrativeLevelTwo.all().count()
    offset = (page - 1) * size
    _administrative_levels_two = await AdministrativeLevelTwo.all().offset(offset).limit(size).values("code", "numeric_code", "name", "administrative_level_one__code")
    return PaginatedResponse[AdministrativeLevelTwoRead](
        count=count,
        page=page,
        size=size,
        data=_administrative_levels_two,
    )


@router.get("/administrative-levels-two/{administrative_level_two}")
async def get_administrative_level_two(administrative_level_two: str):
    _administrative_level_two = await AdministrativeLevelTwo.get(code=administrative_level_two)
    return _administrative_level_two


@router.post("/administrative-levels-two")
async def create_administrative_level_two(
    administrative_level_two: AdministrativeLevelTwoCreate,
):
    _administrative_level_one = await AdministrativeLevelOne.get(code=administrative_level_two.administrative_level_one)
    _administrative_level_two = await AdministrativeLevelTwo.create(
        code=administrative_level_two.code,
        name=administrative_level_two.name,
        administrative_level_one=_administrative_level_one,
    )
    return _administrative_level_two


# @router.get("/city-types")
# async def get_city_types():
#     _city_types = await CityType.all()
#     return _city_types


# @router.get("/city-types/{city_type}")
# async def get_city_type(city_type: str):
#     _city_type = await CityType.get(code=city_type)
#     return _city_type


# @router.post("/city-types")
# async def create_city_type(city_type: CityTypeCreate):
#     _city_type = await CityType.create(
#         code=city_type.code,
#         name=city_type.name,
#         description=city_type.description,
#         population_min=city_type.population_min,
#         population_max=city_type.population_max,
#     )
#     return _city_type


@router.get("/cities", response_model=PaginatedResponse[CityRead], response_model_by_alias=False)
async def get_cities(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    count = await City.all().count()
    offset = (page - 1) * size
    _cities = await City.all().offset(offset).limit(size).values("id", "name", "code_postal", "code_insee", "administrative_level_one__code", "administrative_level_two__code")
    return PaginatedResponse[CityRead](count=count, page=page, size=size, data=_cities)


@router.get("/cities/{city}")
async def get_city(city: str):
    _city = await City.get(id=city)
    return _city


@router.post("/cities")
async def create_city(city: CityCreate):
    # _city_type = await CityType.get(code=city.city_type)
    _administrative_level_one = await AdministrativeLevelOne.get(code=city.administrative_level_one)
    _administrative_level_two = await AdministrativeLevelTwo.get(code=city.administrative_level_two)
    _city = await City.create(
        name=city.name,
        postal_code=city.postal_code,
        insee_code=city.insee_code,
        # city_type=_city_type,
        administrative_level_one=_administrative_level_one,
        administrative_level_two=_administrative_level_two,
    )
    return _city


@router.get("/cities-data")
async def get_cities_data():
    _cities_data = await CityData.all()
    return _cities_data


# TODO: missing schema
# @router.post("/cities-data")
# async def create_city_data(city_data: CityData):
#     _city = await City.get(id=city_data.city)
#     _administrative_level_one = await AdministrativeLevelOne.get(code=city_data.administrative_level_one)
#     _administrative_level_two = await AdministrativeLevelTwo.get(code=city_data.administrative_level_two)
#     _city_data = await CityData.create(
#         city=_city,
#         administrative_level_one=_administrative_level_one,
#         administrative_level_two=_administrative_level_two,
#     )
#     return _city_data


@router.get("cities-data/{city_data}")
async def get_city_data(city_data: str):
    _city_data = await CityData.get(id=city_data)
    return _city_data


@router.get("/street-types")
async def get_street_types():
    _street_types = await StreetType.all()
    return _street_types


@router.get("/street-types/{street_type}")
async def get_street_type(street_type: str):
    _street_type = await StreetType.get(code=street_type)
    return _street_type


@router.post("/street-types")
async def create_street_type(street_type: StreetTypeCreate):
    _street_type = await StreetType.create(code=street_type.code, name=street_type.name, short_name=street_type.short_name)
    return _street_type


@router.get("/streets", response_model=PaginatedResponse[StreetRead], response_model_by_alias=False)
async def get_streets(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Retrieve a list of streets."""
    count = await Street.all().count()
    offset = (page - 1) * size

    _streets = await Street.all().offset(offset).limit(size).values("id", "name", "street_type__code", "city__name")
    return PaginatedResponse[StreetRead](
        count=count,
        page=page,
        size=size,
        data=_streets,
    )


@router.get("/streets/{street}")
async def get_street(street: str):
    _street = await Street.get(id=street)
    return _street


@router.post("/streets")
async def create_street(street: StreetCreate):
    _street_type = await StreetType.get(code=street.street_type)
    _city = await City.get(name=street.city)
    _street = await Street.create(name=street.name, street_type=_street_type, city=_city)
    return _street


@router.get("/addresses/search")
async def search_addresses(address: Annotated[str, Query(...)]):
    if not address:
        return {"detail": "Address is required", "status_code": status.HTTP_400_BAD_REQUEST}

    gov_address_match, is_cached = await Address.search_address_gov(address)

    if gov_address_match:
        t = await Address.api_gov_adresse_connector(gov_address_match["features"][0])
        print(t)
        return {"result": gov_address_match["features"], "is_cached": is_cached}

    return {"message": "searching addresses"}


@router.get("/addresses", response_model=PaginatedResponse[AddressRead], response_model_by_alias=False)
async def get_addresses(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Retrieve a list of addresses."""
    count = await Address.all().count()
    offset = (page - 1) * size
    _addresses = await Address.all().offset(offset).limit(size).values("id", "number", "number_extension", "complement", "latitude", "longitude", "street__name")
    return PaginatedResponse[AddressRead](
        count=count,
        page=page,
        size=size,
        data=_addresses,
    )


@router.get("/addresses/{address}")
async def get_address(address: str):
    _address = await Address.get(id=address)
    return _address


@router.post("/addresses")
async def create_address(address: AddressCreate):
    _address = await Address.create()
    return _address


@router.get("/geo-data")
async def get_geo_data():
    _geo_data = await GeoData.all()
    return _geo_data


@router.get("/geo-data/{geo_data}")
async def get_geo_data_by_id(geo_data: str):
    _geo_data = await GeoData.get(id=geo_data)
    return _geo_data


# @router.post("/geo-data")
# async def create_geo_data(geo_data: "GeoData"):
#     _geo_data = await GeoData.create(
#         geojson=geo_data.geodata,
#         continent=geo_data.continent,
#         country=geo_data.country,
#         administrative_level_one=geo_data.administrative_level_one,
#         administrative_level_two=geo_data.administrative_level_two,
#         city=geo_data.city,
#         street=geo_data.street,
#     )
#     return _geo_data
