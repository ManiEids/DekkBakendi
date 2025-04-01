import scrapy
import re

class NesdekkSpider(scrapy.Spider):
    name = "nesdekk"
    allowed_domains = ["nesdekk.is"]
    # Use a URL with an empty search parameter to get the full catalogue.
    start_urls = [
        "https://nesdekk.is/dekkjaleit/?tyre-filter=1"
    ]
    
    custom_settings = {
        'TELNETCONSOLE_ENABLED': False,
        'DOWNLOAD_TIMEOUT': 30,
        'DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def parse(self, response):
        # Loop over each product in the page.
        for product in response.css("li.product"):
            # Extract the tire's name from the h2 element.
            name = product.css("h2.woocommerce-loop-product__title::text").get()
            if name:
                name = name.strip()
            
            # Extract the price. The selector grabs the text content of the <bdi> element.
            price = product.css("span.price span.woocommerce-Price-amount.amount bdi").xpath("string()").get()
            if price:
                price = price.strip()
            
            # Extract the picture URL from the <img> tag inside the product link.
            picture = product.css("a.woocommerce-LoopProduct-link img::attr(src)").get()
            
            # Extract stock information from the <div class="stock"> element's <strong> text.
            stock = product.css("div.stock strong::text").get()
            if stock:
                stock = stock.strip()
            else:
                stock = "in stock"  # Default value if not explicitly stated
            
            # Extract tire size from the tyre-details container.
            tyre_size = product.css("div.tyre-details a.tyre-size::text").get()
            if tyre_size:
                tyre_size = tyre_size.strip()
            
            # Extract manufacturer from the tyre-details container.
            manufacturer = product.css("div.tyre-details a.tyre-brand::text").get()
            if manufacturer:
                manufacturer = manufacturer.strip()
            
            yield {
                "name": name,
                "price": price,
                "picture": picture,
                "stock": stock,
                "tyre_size": tyre_size,
                "manufacturer": manufacturer,
            }
        
        # Follow pagination: look for a link with class "next page-numbers"
        next_page = response.css("a.next.page-numbers::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
