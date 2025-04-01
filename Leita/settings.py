BOT_NAME = 'Leita'

SPIDER_MODULES = ['Leita.spiders']
NEWSPIDER_MODULE = 'Leita.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8  # Reduced from 16 to be gentler on memory

# Disable cookies for better speed
COOKIES_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {}

# Enable logging
LOG_ENABLED = True
LOG_LEVEL = 'INFO'

# Disable the telnet console to prevent "AlreadyNegotiating" errors
TELNETCONSOLE_ENABLED = False

# Set timeouts to prevent hanging
DOWNLOAD_TIMEOUT = 30
CLOSESPIDER_TIMEOUT = 180  # 3 minutes max

# Enable autothrottle for better performance
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Enable spider middlewares - make sure to use correct path
SPIDER_MIDDLEWARES = {
    'Leita.middlewares.TelnetConsoleFixMiddleware': 100,
    'Leita.middlewares.LeitaSpiderMiddleware': 543,
}

# Configure downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'Leita.middlewares.LeitaDownloaderMiddleware': 543,
}

# Explicitly disable telnet console in multiple places to make sure it's off
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}
