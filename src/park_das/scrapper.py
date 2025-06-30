import json

from typing import List, Dict
from re import search

from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode

from .constants import CarParkNames
from .models import CarPark, UserType


VISITOR_URL = "http://tsu-app.rrooaarr.biz/front/index.html"
WORKER_URL = "http://tsu-app.rrooaarr.biz/front/mitarbeiter.html"
PBW_URL = ("https://www.pbw.de/?menu=parkplatz-finder&profile=kurz-dauer&search="
           "*234%2089081%20Ulm%20Parkhaus%20Helmholtzstra%C3%9Fe%20&anchor=results")

schema = {
    "name": "parking_spaces",
    "baseSelector": "section ul li.green",
    "fields": [
        {
            "name": "name",
            "selector": ".p-text",
            "type": "text",
            "transform": "strip",
            "default": ""
        },
        {
            "name": "p_number",
            "selector": ".p-number",
            "type": "text",
            "transform": "strip",
            "default": ""
        },
        {
            "name": "free_spaces",
            "selector": ".free-number",
            "type": "text",
            "transform": "strip",
            "default": ""
        },
        {
            "name": "total_spaces",
            "selector": "a > small",
            "type": "text",
            "transform": "strip",
            "default": ""
        }
    ]
}

helmholtz_schema = {
    "name": "helmholtz_parking",
    "baseSelector": "div.finder-detail",
    "fields": [
        {
            "name": "total_spaces",
            "selector": "div.finder-detail-left img[alt^='Stellplatzanzahl'] + div",
            "type": "text",
            "transform": "strip",
            "default": ""
        },
        {
            "name": "free_spaces",
            "selector": "h2 span[style*='background-color:#3FA535']",
            "type": "text",
            "transform": "strip",
            "default": "0"
        }
    ]
}

config = CrawlerRunConfig(
    wait_until="networkidle",
    cache_mode=CacheMode.BYPASS,
    extraction_strategy=JsonCssExtractionStrategy(schema),
)

config_helmholtz = config.clone(
    extraction_strategy=JsonCssExtractionStrategy(helmholtz_schema)
)

parking_data: Dict[UserType, List[CarPark]] = {}

async def scrape_data(is_visitor: bool = False, scrape_all: bool = False) -> List[CarPark]:
    """
    Asynchronously fetches parking space data. This is only used for the interval
    updates of the parking spaces. Use `get_data` to retrieve the data.

    :param is_visitor: Flag that controls if data is fetched for visitors / workers
    :param scrape_all: Flag that controls whether Helmholtz parking is fetched or not
    :return: A list of CarPark objects containing the fetched data.
    """
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=VISITOR_URL if is_visitor else WORKER_URL,
            config=config
        )

        data = []
        if not result.success: # type: ignore
            print("Default-Crawl failed:", result.error_message) # type: ignore
            return data

        for item in json.loads(result.extracted_content): # type: ignore
            name: str = item.get("name", "")
            numbers: str = item.get("p_number", "")
            free_spaces: str = item.get("free_spaces", "")
            total_spaces: str = search(r'\d+', item.get("total_spaces", "")).group() # type: ignore

            if name == "" or numbers == "" or free_spaces == "":
                continue

            try:
                data.append(
                    CarPark(
                        CarParkNames.parse(f"{name} {numbers}"),
                        int(free_spaces),
                        int(total_spaces),
                        is_visitor
                    )
                )
            except KeyError:
                print(f"Unknown car park name: {name} {numbers}")
                continue

        if not scrape_all:
            return data

        result = await crawler.arun(
            url=PBW_URL,
            config=config_helmholtz
        )

        if not result.success: # type: ignore
            print("PBW-Crawl failed:", result.error_message) # type: ignore
            return data

        item = json.loads(result.extracted_content)[0] # type: ignore
        if not item["total_spaces"] or not item["free_spaces"]:
            return data

        data.append(
            CarPark(
                CarParkNames.HE,
                int(item.get("free_spaces", 0)),
                int(item.get("total_spaces", 0)),
                is_visitor
            )
        )

        return data

async def fetch_data():
    """
    Updates the global parking_data list with the latest parking space data.
    """
    data = await scrape_data(is_visitor=True, scrape_all=True)
    data.extend([p for p in await scrape_data() if p not in data])

    for tp in UserType:
        match tp:
            case UserType.VISITOR:
                parking_data[tp] = [p for p in data if p.is_visitor and not p.is_inner_city]
            case UserType.WORKER:
                parking_data[tp] = [p for p in data if not p.is_inner_city]
            case UserType.CITY:
                parking_data[tp] = [p for p in data if p.is_inner_city]
            case _:
                parking_data[tp] = data

async def get_data(for_type: UserType) -> List[CarPark]:
    """
    Filters and retrieves parking data based on the type of user.

    :param for_type: User type for which to get the parking spot list
    :return: A list of parking spots for the specified user type
    """
    return parking_data[for_type]
