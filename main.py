import os
import asyncio
import logging
import schedule
import requests
from datetime import datetime
from telegram import Bot, TelegramError
from config import BOT_TOKEN, GROUP_IDS, CRYPTO_INTERVAL, SPORTS_INTERVAL, NEWS_API_KEY

# -------------------- Logging --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# -------------------- Async NewsBot --------------------
class NewsBot:
    def __init__(self, token):
        self.bot = Bot(token=token)
        self.group_ids = [gid.strip() for gid in GROUP_IDS if gid.strip()]

    # -------- Bot connection test --------
    async def test_bot(self):
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Bot connected as @{bot_info.username}")
            return True
        except TelegramError as e:
            logger.error(f"❌ Bot connection failed: {e}")
            return False

    # -------- Group access test --------
    async def test_group_access(self):
        logger.info("🔍 Testing group access...")
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(chat_id=group_id, text=f"✅ Test message to group {group_id}")
                logger.info(f"✅ Access OK for {group_id}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Cannot send to group {group_id}: {e}")
        logger.info("🔎 Group access test complete.")

    # -------- Send test message --------
    async def send_test_message(self):
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(chat_id=group_id, text="🚀 Bot is active and fetching real news!")
                logger.info(f"✅ Test sent to {group_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send test to {group_id}: {e}")

    # -------- Fetch crypto news --------
    async def fetch_crypto_news(self):
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if "Data" not in data or len(data["Data"]) == 0:
                return None

            article = data["Data"][0]  # first news item
            return {
                "title": article.get("title", "Crypto News"),
                "desc": article.get("body", ""),
                "url": article.get("url", ""),
                "image": article.get("imageurl", "https://cryptologos.cc/logos/bitcoin-btc-logo.png")
            }
        except Exception as e:
            logger.error(f"❌ Error fetching crypto news: {e}")
            return None

    # -------- Fetch sports news --------
    async def fetch_sports_news(self):
        if not NEWS_API_KEY:
            return None
        url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&pageSize=1&apiKey={NEWS_API_KEY}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if "articles" in data and len(data["articles"]) > 0:
                article = data["articles"][0]
                return {
                    "title": article.get("title", "Sports News"),
                    "desc": article.get("description", ""),
                    "url": article.get("url", ""),
                    "image": article.get("urlToImage", "https://upload.wikimedia.org/wikipedia/commons/d/d7/Soccerball.svg")
                }
        except Exception as e:
            logger.error(f"❌ Error fetching sports news: {e}")
            return None

    # -------- Post crypto news --------
    async def post_crypto_news(self):
        news = await self.fetch_crypto_news()
        if news:
            caption = f"🪙 <b>{news['title']}</b>\n{news['desc']}\n<a href='{news['url']}'>Read more</a>"
            await self._send_photo_to_all(news['image'], caption)
        else:
            await self._send_text_to_all("🪙 Crypto News\n\nUnable to fetch latest updates. Stay tuned!")

    # -------- Post sports news --------
    async def post_sports_news(self):
        news = await self.fetch_sports_news()
        if news:
            caption = f"⚽ <b>{news['title']}</b>\n{news['desc']}\n<a href='{news['url']}'>Read more</a>"
            await self._send_photo_to_all(news['image'], caption)
        else:
            await self._send_text_to_all("⚽ Sports News\n\nUnable to fetch latest updates. Stay tuned!")

    # -------- Helpers --------
    async def _send_text_to_all(self, message):
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(chat_id=group_id, text=message, parse_mode="HTML")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Failed to send to {group_id}: {e}")

    async def _send_photo_to_all(self, photo_url, caption):
        for group_id in self.group_ids:
            try:
                await self.bot.send_photo(chat_id=group_id, photo=photo_url, caption=caption, parse_mode="HTML")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Failed to send to {group_id}: {e}")

# -------------------- Scheduler --------------------
async def run_scheduler(news_bot):
    while True:
        schedule.run_pending()
        await asyncio.sleep(30)

# -------------------- Main --------------------
async def main():
    logger.info("🤖 Starting Telegram News Bot...")

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found")
        return
    if not GROUP_IDS:
        logger.error("❌ No GROUP_IDS found")
        return

    bot = NewsBot(BOT_TOKEN)
    if not await bot.test_bot():
        return

    await bot.test_group_access()
    await bot.send_test_message()

    # Schedule every 1 minute
    schedule.every(CRYPTO_INTERVAL).minutes.do(lambda: asyncio.create_task(bot.post_crypto_news()))
    schedule.every(SPORTS_INTERVAL).minutes.do(lambda: asyncio.create_task(bot.post_sports_news()))

    logger.info("🚀 Sending initial posts...")
    await bot.post_crypto_news()
    await asyncio.sleep(3)
    await bot.post_sports_news()

    logger.info("✅ Bot is now running and scheduled!")
    await run_scheduler(bot)

# -------------------- Entry --------------------
if __name__ == "__main__":
    asyncio.run(main())
