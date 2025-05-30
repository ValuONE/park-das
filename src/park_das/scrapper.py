import json
import asyncio
from typing import List
from re import search

from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode

from .constants import CarParkNames
from .models import CarPark

VISITOR_URL = "http://tsu-app.rrooaarr.biz/front/index.html"
WORKER_URL = "http://tsu-app.rrooaarr.biz/front/mitarbeiter.html"

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

extraction_strategy = JsonCssExtractionStrategy(schema)

config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    extraction_strategy=extraction_strategy,
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
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(
            url=VISITOR_URL if is_visitor else WORKER_URL,

            config=config
        )

        parking_data = []
        if not result.success:
            print("Crawl failed:", result.error_message)
            return parking_data

        for item in json.loads(result.extracted_content):
            name : str = item["name"]
            numbers : str = item["p_number"]
            free_spaces : str = item["free_spaces"]
            total_spaces : str = search(r'\d+', item["total_spaces"]).group()

            if not name or not numbers or not free_spaces:
                continue

            if name == "" or numbers == "" or free_spaces == "":
                continue

            if numbers.startswith("M"):
                continue

            parking_data.append(
                CarPark(CarParkNames.parse(f"{name} {numbers}"),
                        int(free_spaces), int(total_spaces))
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
