import json

from typing import List
from re import search

from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode

from .constants import CarParkNames, VISITOR_PARK_LOCATIONS, WORKER_PARK_LOCATIONS
from .models import CarPark


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
            "default": ""
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

parking_data: List[CarPark] = []


async def scrape_data(is_visitor: bool = False, scrape_all: bool = False) -> List[CarPark]:
    """
    Asynchronously fetches parking space data. This is only used for the interval
    updates of the parking spaces. Use `get_data` to retrieve the data.

    Args:
        is_visitor (bool): If True, fetch data for visitor parking spaces.
                           If False, fetch data for worker parking spaces.
        scrape_all (bool): If True, also fetch data for the Helmholtz parking space.

    Returns:
        List[CarPark]: A list of CarPark objects containing the fetched data.
    """
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=VISITOR_URL if is_visitor else WORKER_URL,
            config=config
        )

        data = []
        if not result.success:
            print("Default-Crawl failed:", result.error_message)
            return data

        for item in json.loads(result.extracted_content):
            name: str = item["name"]
            numbers: str = item["p_number"]
            free_spaces: str = item["free_spaces"]
            total_spaces: str = search(r'\d+', item["total_spaces"]).group()

            if not name or not numbers or not free_spaces:
                continue

            if name == "" or numbers == "" or free_spaces == "":
                continue

            try:
                data.append(
                    CarPark(CarParkNames.parse(f"{name} {numbers}"),
                            int(free_spaces), int(total_spaces))
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

        if not result.success:
            print("PBW-Crawl failed:", result.error_message)
            return data

        item = json.loads(result.extracted_content)[0]
        if not item["total_spaces"] or not item["free_spaces"]:
            return data

        data.append(
            CarPark(CarParkNames.HE,
                    int(item["free_spaces"]), int(item["total_spaces"]))
        )

        return data


async def fetch_data():
    """
    Updates the global parking_data list with the latest parking space data.

    Returns:
        List[CarPark]: A list of CarPark objects containing the fetched data.
    """
    visitor_data = await scrape_data(is_visitor=True, scrape_all=True)
    worker_data = await scrape_data()

    global parking_data
    parking_data = list({p.name: p for p in (visitor_data + worker_data)}.values())


async def get_data(is_visitor: bool) -> List[CarPark]:
    """
    Filters and retrieves parking data based on the type of user.

    Args:
        is_visitor (bool): If True, retrieves data for visitor parking spaces.
                           If False, retrieves data for worker parking spaces.

    Returns:
        List[CarPark]: A list of CarPark objects filtered by the specified user type.
                       Visitor parking spaces are filtered using `VISITOR_PARK_LOCATIONS`,
                       while worker parking spaces are filtered using `WORKER_PARK_LOCATIONS`.
    """
    if is_visitor:
        return [p for p in parking_data if p.name in VISITOR_PARK_LOCATIONS]

    return [p for p in parking_data if p.name in WORKER_PARK_LOCATIONS]
