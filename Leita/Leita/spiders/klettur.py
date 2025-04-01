import scrapy

class TiresSpider(scrapy.Spider):
    name = "klettur"
    allowed_domains = ["bud.klettur.is"]
    
    # Add custom settings to disable telnet console and improve reliability
    custom_settings = {
        'TELNETCONSOLE_ENABLED': False,  # Disable telnet console to prevent errors
        'DOWNLOAD_TIMEOUT': 30,
        'DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'ROBOTSTXT_OBEY': False,  # Often more reliable to disable this
    }
    
    # Instead of using start_urls, we'll override start_requests to include headers.
    def start_requests(self):
        url = "https://bud.klettur.is/wp-content/themes/bud.klettur.is/kallkerfi/dekkjalisti/get_tires.php?getalltires=true"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Referer": "https://www.klettur.is/",
            "Origin": "https://www.klettur.is",
        }
        self.logger.info(f"Starting request to: {url}")
        yield scrapy.Request(url=url, headers=headers, callback=self.parse, errback=self.handle_error)
    
    def parse(self, response):
        # Since this URL returns JSON data, we can parse it directly.
        try:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            self.logger.info(f"Successfully received {count} tire entries")
            
            # For each tire entry in the JSON, yield it.
            for tire in data:
                yield tire
                
            self.logger.info(f"Completed processing {count} items from Klettur")
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
    
    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.getErrorMessage()}")
