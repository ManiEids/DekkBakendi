"""
Common settings module that can be imported by all spiders.
"""

# Settings to improve reliability and prevent telnet console errors
COMMON_SETTINGS = {
    'TELNETCONSOLE_ENABLED': False,  # Disable telnet console to prevent errors
    'DOWNLOAD_TIMEOUT': 30,          # Reasonable timeout
    'DOWNLOAD_DELAY': 1.0,           # Polite crawling
    'CONCURRENT_REQUESTS_PER_DOMAIN': 2,  # Avoid overloading servers
    'ROBOTSTXT_OBEY': False,         # Often more reliable
    'LOG_LEVEL': 'INFO',             # Show useful information
    'COOKIES_ENABLED': False,        # Disable cookies for better performance
    'RETRY_TIMES': 3,                # Retry failed requests
    'HTTPERROR_ALLOWED_CODES': [404, 403],  # Continue on some error codes
}

def get_common_settings(additional_settings=None):
    """
    Get the common settings with optional additional settings.
    """
    settings = COMMON_SETTINGS.copy()
    if additional_settings:
        settings.update(additional_settings)
    return settings
