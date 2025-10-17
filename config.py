import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_IDS = [
    int(group_id.strip()) for group_id in os.getenv('GROUP_IDS', '').split(',') 
    if group_id.strip()
]

# News API Configuration
CRYPTO_NEWS_API = "https://api.coingecko.com/api/v3/news"
SPORTS_NEWS_API = "https://newsapi.org/v2/top-headlines?category=sports&apiKey={}"

# NewsAPI.org key (get free key from https://newsapi.org)
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# Posting intervals (in minutes)
CRYPTO_INTERVAL = 60  # 1 hour
SPORTS_INTERVAL = 30  # 30 minutes

# Maximum groups
MAX_GROUPS = 10
