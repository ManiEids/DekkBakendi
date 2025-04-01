import scrapy
import re
from itertools import product

class DekkjahollinSpider(scrapy.Spider):
    name = "dekkjahollin"
    allowed_domains = ["dekkjahollin.is"]

    # Simplified mapping with fewer combinations to complete faster
    rim_mapping = {
        "15": {
            "widths": ["195", "205", "215"],
            "heights": ["65", "60", "55"]
        },
        "16": {
            "widths": ["205", "215", "225"],
            "heights": ["60", "55", "50"]
        },
        "17": {
            "widths": ["215", "225", "235"],
            "heights": ["55", "50", "45"]
        }
    }

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': None,
        },
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'DOWNLOAD_TIMEOUT': 30,  # 30 seconds timeout
        'CLOSESPIDER_PAGECOUNT': 100,  # Limit to 100 pages
        'CLOSESPIDER_TIMEOUT': 180,  # 3 minute timeout
    }

    def start_requests(self):
        base_url = "https://www.dekkjahollin.is/is/leit?q={size}&t%5B%5D=store"
        # Iterate over the mapping: for each rim, iterate over its allowed widths and heights.
        for rim, specs in self.rim_mapping.items():
            for width in specs["widths"]:
                for height in specs["heights"]:
                    size = f"{width}/{height}R{rim}"
                    url = base_url.format(size=size)
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        errback=self.errback_httpbin,
                        meta={'tire_size': size, 'dont_redirect': True}
                    )

    def parse(self, response):
        tire_size = response.meta.get("tire_size", "Unknown")
        self.logger.info(f"Parsing {response.url} for tire size: {tire_size}")
        
        products = response.css("li.store.product")
        if not products:
            self.logger.debug(f"No products found for size: {tire_size}")
        
        for product in products:
            title = product.css("div.content a.title::text").get()
            if not title:
                continue
            title = title.strip()
            
            price_text = product.css("div.content div.priceBox span.price::text").get()
            price = None
            if price_text:
                price = re.sub(r"(Tilboðsverð:|Verð:)\s*", "", price_text)
                price = re.sub(r"kr\.?", "", price).strip()

            stock = product.css("div.content div.stock::text").get()
            stock = stock.strip() if stock else "Unknown"
            
            picture = None
            style_attr = product.css("div.content div.image::attr(style)").get()
            if style_attr:
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style_attr)
                if match:
                    picture = match.group(1).strip()
                    if picture.startswith("/"):
                        picture = "https://www.dekkjahollin.is" + picture
            
            manufacturer = title.split()[0] if title else None
            
            yield {
                "title": title,
                "tire_size": tire_size,
                "price": price,
                "stock": stock,
                "picture": picture,
                "manufacturer": manufacturer,
            }
        
        # Follow pagination if available
        next_page = response.css("ul.pagination li.next a::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse,
                errback=self.errback_httpbin,
                meta={'tire_size': tire_size}
            )

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))
