BOT_NAME = 'Leita'

SPIDER_MODULES = ['Leita.spiders']
NEWSPIDER_MODULE = 'Leita.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16

# Disable cookies for better speed
COOKIES_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {}

# Enable logging
LOG_ENABLED = True
LOG_LEVEL = 'INFO'
