import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_IDS = os.getenv("GROUP_IDS", "").split(",")

# News fetch intervals (in minutes)
CRYPTO_INTERVAL = int(os.getenv("CRYPTO_INTERVAL", 1))
SPORTS_INTERVAL = int(os.getenv("SPORTS_INTERVAL", 1))

# Optional API keys (if you use them)
CRYPTO_API_KEY = os.getenv("CRYPTO_API_KEY")
SPORTS_API_KEY = os.getenv("SPORTS_API_KEY")
