import os
import time
import asyncio
import logging
import schedule
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from config import BOT_TOKEN, GROUP_IDS, CRYPTO_INTERVAL, SPORTS_INTERVAL

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
        """Test if the bot token works"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Bot connected as @{bot_info.username}")
            return True
        except TelegramError as e:
            logger.error(f"❌ Bot connection failed: {e}")
            return False

    async def test_group_access(self):
        """Check which groups the bot can send messages to"""
        logger.info("🔍 Testing group access...")
        for group_id in self.group_ids:
            try:
                test_msg = f"✅ Test message to group {group_id} at {datetime.now().strftime('%H:%M:%S')}"
                msg = await self.bot.send_message(chat_id=group_id, text=test_msg)
                logger.info(f"✅ Success: {group_id} (message_id={msg.message_id})")
                await asyncio.sleep(1)
            except TelegramError as e:
                logger.error(f"❌ Cannot send to group {group_id}: {e}")
            except Exception as e:
                logger.error(f"⚠️ Unexpected error for group {group_id}: {e}")
        logger.info("🔎 Group access test complete.")

    async def send_test_message(self):
        """Send a test message to all groups"""
        for group_id in self.group_ids:
            try:
                msg = await self.bot.send_message(chat_id=group_id, text="🚀 Bot is now active and ready!")
                logger.info(f"✅ Sent to {group_id} (message_id={msg.message_id})")
            except Exception as e:
                logger.error(f"❌ Failed to send to {group_id}: {e}")

    # -------------------- News Posting --------------------
    async def post_crypto_news(self):
        news = f"🪙 *Crypto News Update* — {datetime.now().strftime('%H:%M:%S')}\nBTC and ETH showing stability today."
        await self._send_to_all_groups(news)

    async def post_sports_news(self):
        news = f"⚽ *Sports News Update* — {datetime.now().strftime('%H:%M:%S')}\nTop teams preparing for this weekend's matches!"
        await self._send_to_all_groups(news)

    async def _send_to_all_groups(self, message):
        """Send the message to all configured groups"""
        success = 0
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(chat_id=group_id, text=message, parse_mode="Markdown")
                success += 1
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Failed to send to {group_id}: {e}")
        logger.info(f"📊 Delivery Summary: {success}/{len(self.group_ids)} successful")

# -------------------- Async Scheduler --------------------
async def run_scheduled(news_bot):
    """Run schedule jobs in async loop"""
    while True:
        schedule.run_pending()
        await asyncio.sleep(30)

# -------------------- Main --------------------
async def main():
    logger.info("🤖 Starting Telegram News Bot...")

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables")
        return
    if not GROUP_IDS:
        logger.error("❌ No GROUP_IDS configured")
        return

    news_bot = NewsBot(BOT_TOKEN)

    if not await news_bot.test_bot():
        logger.error("❌ Bot initialization failed")
        return

    logger.info(f"✅ Bot initialized successfully")
    logger.info(f"📋 Monitoring {len(news_bot.group_ids)} groups")

    # Test group access
    await news_bot.test_group_access()

    # Send test message
    await news_bot.send_test_message()

    # Schedule jobs
    logger.info(f"⏰ Crypto news every {CRYPTO_INTERVAL} min | Sports every {SPORTS_INTERVAL} min")
    schedule.every(CRYPTO_INTERVAL).minutes.do(lambda: asyncio.create_task(news_bot.post_crypto_news()))
    schedule.every(SPORTS_INTERVAL).minutes.do(lambda: asyncio.create_task(news_bot.post_sports_news()))

    # Send first posts immediately
    logger.info("🚀 Sending initial posts immediately...")
    await news_bot.post_crypto_news()
    await asyncio.sleep(3)
    await news_bot.post_sports_news()

    logger.info("✅ Bot is now running and scheduled!")

    await run_scheduled(news_bot)

# -------------------- Entry Point --------------------
if __name__ == "__main__":
    asyncio.run(main())
