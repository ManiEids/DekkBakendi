import scrapy
import re

class DekkjasalanSpider(scrapy.Spider):
    name = "dekkjasalan"
    allowed_domains = ["dekkjasalan.is"]
    # Start with an empty search query to retrieve the full catalogue.
    start_urls = [
        "https://dekkjasalan.is/?s="
    ]
    
    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/134.0.0.0 Safari/537.36'),
        },
        # Uncomment the next line if you need to override robots.txt
        # 'ROBOTSTXT_OBEY': False,
    }
    
    def parse(self, response):
        # Log a snippet of the HTML for debugging.
        body_snippet = response.text[:500]
        self.logger.info(f"DEKKJASALAN HTML snippet: {body_snippet}")
        
        # Each product is within an <article> element with class "result".
        articles = response.css("article.result")
        self.logger.info(f"Found {len(articles)} articles on this page.")
        
        for product in articles:
            # Extract the product name from <h2 class="title"><a>.
            title = product.css("h2.title a::text").get()
            if title:
                title = title.strip()
            
            # Use a regex to extract the tire size (formats like "205-55-16" or "205/55/16").
            tire_size = None
            if title:
                size_match = re.search(r"(\d{3}[-/]\d{2}[-/]\d+)", title)
                if size_match:
                    tire_size = size_match.group(1)
            
            # Extract the price from the element containing a <bdi> tag.
            price = product.css("div.commerce_excerpt11 .woocommerce-Price-amount bdi::text").get()
            if price:
                price = price.strip()
            else:
                # Fallback to any price element.
                price = product.css("span.price::text").get(default="").strip()
            
            # Extract inventory information from the element containing text like "Fjöldi: 4 stk."
            inventory_text = product.css("div.commerce_excerpt33").xpath("string()").get()
            inventory = 0
            if inventory_text:
                inv_match = re.search(r"Fjöldi:\s*(\d+)", inventory_text)
                if inv_match:
                    inventory = int(inv_match.group(1))
            # Do not skip products with zero inventory; we want to yield them with stock info.
            
            # Extract the product picture URL from the <img> tag inside the product link.
            picture = product.css("a img::attr(src)").get()
            if picture:
                picture = picture.strip()
            
            # Attempt to derive the manufacturer by splitting the title after the tire size.
            manufacturer = None
            if tire_size and title:
                after_size = title[len(tire_size):].strip()
                if after_size:
                    manufacturer = after_size.split()[0]
            
            yield {
                "title": title,
                "tire_size": tire_size,
                "price": price,
                "inventory": inventory,
                "stock": "in stock" if inventory > 0 else "out of stock",
                "picture": picture,
                "manufacturer": manufacturer,
            }
        
        # Follow pagination if a "next" link exists.
        next_page = response.css("a.next.page-numbers::attr(href)").get()
        if next_page:
            self.logger.info(f"Following pagination to: {next_page}")
            yield scrapy.Request(next_page, callback=self.parse)
