import json
import asyncio
from typing import List
from re import search

from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode

from .constants import CarParkNames
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

async def fetch_data_async(is_visitor: bool) -> List[CarPark]:
    """
    Asynchronously fetches parking space data.

    Args:
        is_visitor (bool): If True, fetch data for visitor parking spaces.
                           If False, fetch data for worker parking spaces.

    Returns:
        List[CarPark]: A list of CarPark objects containing the fetched data.
    """
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=VISITOR_URL if is_visitor else WORKER_URL,
            config=config
        )

        parking_data = []
        if not result.success:
            print("Default-Crawl failed:", result.error_message)
            return parking_data

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
                parking_data.append(
                    CarPark(CarParkNames.parse(f"{name} {numbers}"),
                            int(free_spaces), int(total_spaces))
                )
            except KeyError:
                print(f"Unknown car park name: {name} {numbers}")
                continue

        result = await crawler.arun(
            url=PBW_URL,
            config=config_helmholtz
        )

        if not result.success:
            print("PBW-Crawl failed:", result.error_message)
            return parking_data

        item = json.loads(result.extracted_content)[0]
        if not item["total_spaces"] or not item["free_spaces"]:
            return parking_data

        parking_data.append(
            CarPark(CarParkNames.HE,
                    int(item["free_spaces"]), int(item["total_spaces"]))
        )

        return parking_data


def fetch_data(is_visitor: bool) -> List[CarPark]:
    """
        Synchronously fetches parking space data by 
        wrapping the asynchronous function using asyncio. 
    
        Args:
            is_visitor (bool): If True, fetch data for visitor parking spaces. 
                               If False, fetch data for worker parking spaces.
    
        Returns:
            List[CarPark]: A list of CarPark objects containing the fetched data.
    """
    return asyncio.run(fetch_data_async(is_visitor))
