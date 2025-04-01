import scrapy
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class MitraTiresSpider(scrapy.Spider):
    name = "mitra"
    allowed_domains = ["mitra.is"]
    start_urls = ["https://mitra.is/api/tires/?page=1"]

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        },
        'TELNETCONSOLE_ENABLED': False,  # Disable telnet console to prevent errors
        'DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_TIMEOUT': 30,
        'CLOSESPIDER_TIMEOUT': 180,  # 3 minutes max
    }

    def __init__(self, *args, **kwargs):
        super(MitraTiresSpider, self).__init__(*args, **kwargs)
        self.seen_ids = set()
        self.items_count = 0
        self.page_count = 0

    def parse(self, response):
        self.page_count += 1
        self.logger.info(f"Processing page {self.page_count}: {response.url}")
        
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Error parsing JSON: {str(e)}")
            return

        if not data:
            self.logger.info(f"No data returned on page {self.page_count}. Stopping pagination.")
            return

        new_items_count = 0
        for tire in data:
            product_id = tire.get("product_id")
            if not product_id:
                continue
            if product_id in self.seen_ids:
                continue
            self.seen_ids.add(product_id)

            try:
                inventory = int(tire.get("inventory", 0))
            except Exception:
                inventory = 0
            price = tire.get("price", "").strip()
            width = tire.get("width", "").strip()
            profile = tire.get("aspect_ratio", "").strip()
            rim = tire.get("diameter", "").strip()
            title = tire.get("title", "").strip()
            manufacturer = title.split()[0] if title else None
            picture = tire.get("card_image", "").strip()
            if picture.startswith("//"):
                picture = "https:" + picture

            yield {
                "product_id": product_id,
                "title": title,
                "manufacturer": manufacturer,
                "price": price,
                "width": width,
                "profile": profile,
                "rim": rim,
                "picture": picture,
                "inventory": inventory,
                "stock": "in stock" if inventory > 0 else "out of stock",
            }
            new_items_count += 1
            self.items_count += 1

        self.logger.info(f"Found {new_items_count} new items on page {self.page_count} (total: {self.items_count})")

        # If no new items were found on this page, assume duplicates and stop.
        if new_items_count == 0:
            self.logger.info("No new items on this page, stopping pagination.")
            return

        # Otherwise, paginate by incrementing the "page" parameter.
        parsed = urlparse(response.url)
        qs = parse_qs(parsed.query)
        current_page = int(qs.get("page", ["1"])[0])
        next_page = current_page + 1
        
        # Limit to 10 pages to prevent overloading
        if next_page > 10:
            self.logger.info("Reached max page limit (10), stopping pagination.")
            return
            
        qs["page"] = [str(next_page)]
        new_query = urlencode(qs, doseq=True)
        next_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        self.logger.info(f"Following next page: {next_url}")
        yield scrapy.Request(next_url, callback=self.parse)
