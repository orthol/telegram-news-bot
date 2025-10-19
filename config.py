import os

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Comma-separated group IDs (e.g. "-1001234567890,-1009876543210")
GROUP_IDS = os.getenv("GROUP_IDS", "").split(",")

# Update intervals in minutes
CRYPTO_INTERVAL = int(os.getenv("CRYPTO_INTERVAL", 120))
SPORTS_INTERVAL = int(os.getenv("SPORTS_INTERVAL", 120))

# NewsAPI key (optional but required for sports news)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Optional: for CoinGecko (no API key required)
CRYPTO_NEWS_API = "https://api.coingecko.com/api/v3/news"
