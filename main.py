import os
import time
import asyncio
import logging
import schedule
import requests
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from config import BOT_TOKEN, GROUP_IDS, CRYPTO_INTERVAL, SPORTS_INTERVAL, NEWS_API_KEY

# -------------------- Logging --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# -------------------- Async NewsBot Class --------------------
class NewsBot:
    def __init__(self, token):
        self.bot = Bot(token=token)
        self.group_ids = [gid.strip() for gid in GROUP_IDS if gid.strip()]

    async def test_bot(self):
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Bot connected as @{bot_info.username}")
            return True
        except TelegramError as e:
            logger.error(f"❌ Bot connection failed: {e}")
            return False

    async def test_group_access(self):
        logger.info("🔍 Testing group access...")
        for group_id in self.group_ids:
            try:
                test_msg = f"✅ Test message to group {group_id} at {datetime.now().strftime('%H:%M:%S')}"
                await self.bot.send_message(chat_id=group_id, text=test_msg)
                logger.info(f"✅ Access OK for {group_id}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Cannot send to group {group_id}: {e}")
        logger.info("🔎 Group access test complete.")

    async def send_test_message(self):
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(chat_id=group_id, text="🚀 Bot is active and fetching real news!")
                logger.info(f"✅ Sent to {group_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send test to {group_id}: {e}")

    # -------------------- Real News Fetchers --------------------
    async def fetch_crypto_news(self):
        """Fetch real crypto news from CoinGecko"""
        url = "https://api.coingecko.com/api/v3/news"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and "data" in data and len(data["data"]) > 0:
                    article = data["data"][0]
                    title = article.get("title", "Latest Crypto News")
                    desc = article.get("description", "No description.")
                    link = article.get("url", "")
                    return f"🪙 *Crypto News*\n\n*{title}*\n{desc}\n\n🔗 [Read More]({link})"
        except Exception as e:
            logger.error(f"❌ Error fetching crypto news: {e}")
        return "🪙 *Crypto News*\n\nUnable to fetch latest updates. Stay tuned!"

    async def fetch_sports_news(self):
        """Fetch real sports news using NewsAPI"""
        if not NEWS_API_KEY:
            return "⚽ *Sports News*\n\nNo NewsAPI key configured."

        url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&pageSize=1&apiKey={NEWS_API_KEY}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "articles" in data and len(data["articles"]) > 0:
                    article = data["articles"][0]
                    title = article.get("title", "Latest Sports News")
                    desc = article.get("description", "")
                    link = article.get("url", "")
                    return f"⚽ *Sports News*\n\n*{title}*\n{desc}\n\n🔗 [Read More]({link})"
        except Exception as e:
            logger.error(f"❌ Error fetching sports news: {e}")
        return "⚽ *Sports News*\n\nUnable to fetch latest sports updates."

    # -------------------- Posting --------------------
    async def post_crypto_news(self):
        msg = await self.fetch_crypto_news()
        await self._send_to_all_groups(msg)

    async def post_sports_news(self):
        msg = await self.fetch_sports_news()
        await self._send_to_all_groups(msg)

    async def _send_to_all_groups(self, message):
        success = 0
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(
                    chat_id=group_id, 
                    text=message, 
                    parse_mode="Markdown", 
                    disable_web_page_preview=True
                )
                success += 1
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Failed to send to {group_id}: {e}")
        logger.info(f"📊 Delivery Summary: {success}/{len(self.group_ids)} successful")

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

    schedule.every(CRYPTO_INTERVAL).minutes.do(lambda: asyncio.create_task(bot.post_crypto_news()))
    schedule.every(SPORTS_INTERVAL).minutes.do(lambda: asyncio.create_task(bot.post_sports_news()))

    logger.info("🚀 Sending initial posts...")
    await bot.post_crypto_news()
    await asyncio.sleep(3)
    await bot.post_sports_news()

    logger.info("✅ Running schedule loop...")
    await run_scheduler(bot)

if __name__ == "__main__":
    asyncio.run(main())
