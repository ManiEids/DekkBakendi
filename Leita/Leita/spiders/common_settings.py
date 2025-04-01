"""
Common settings to be imported by all spiders
"""

# Disable the telnet console to prevent "AlreadyNegotiating" errors
TELNETCONSOLE_ENABLED = False

# Increase timeouts and limit crawl time
DOWNLOAD_TIMEOUT = 30
CLOSESPIDER_TIMEOUT = 180  # 3 minutes max
CLOSESPIDER_PAGECOUNT = 200  # Limit pages to prevent memory issues

# Set concurrency and autothrottle settings for better behavior
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1.0
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
