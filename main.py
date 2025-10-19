import os
import time
import asyncio
import logging
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
        # Ensure group IDs are integers
        self.group_ids = [int(gid.strip()) for gid in GROUP_IDS if gid.strip()]
        self.running = True
        logger.info(f"📋 Bot will post to {len(self.group_ids)} groups")

    async def test_bot(self):
        """Test if bot can connect"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Bot connected as @{bot_info.username} (ID: {bot_info.id})")
            return True
        except TelegramError as e:
            logger.error(f"❌ Bot connection failed: {e}")
            return False

    async def test_group_access(self):
        """Test access to each group"""
        logger.info("🔍 Testing group access...")
        for group_id in self.group_ids:
            try:
                # First try to get chat info
                chat = await self.bot.get_chat(group_id)
                logger.info(f"   ✅ Group {group_id}: {chat.title} ({chat.type})")
                
                # Then send test message
                test_msg = f"🤖 Bot Test\n\nGroup: {chat.title}\nTime: {datetime.now().strftime('%H:%M:%S')}\n\nIf you see this, bot is working!"
                await self.bot.send_message(chat_id=group_id, text=test_msg)
                logger.info(f"   ✅ Message delivered to {group_id}")
                
            except Exception as e:
                logger.error(f"   ❌ Failed group {group_id}: {e}")
            
            await asyncio.sleep(2)  # Rate limiting
        
        logger.info("🔍 Group access test complete.")

    # -------------------- Real News Fetchers --------------------
    async def fetch_crypto_news(self):
        """Fetch real crypto news from CoinGecko"""
        url = "https://api.coingecko.com/api/v3/news"
        try:
            logger.info("📡 Fetching crypto news...")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and "data" in data and len(data["data"]) > 0:
                    article = data["data"][0]
                    title = article.get("title", "Latest Crypto News").strip()
                    desc = article.get("description", "No description available.").strip()
                    link = article.get("url", "")
                    
                    # Clean and format
                    if len(desc) > 300:
                        desc = desc[:300] + "..."
                    
                    message = f"🚀 **Crypto News Update** 🚀\n\n"
                    message += f"**{title}**\n\n"
                    message += f"{desc}\n\n"
                    
                    if link:
                        message += f"[📖 Read Full Article]({link})\n\n"
                    
                    message += f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    
                    logger.info("✅ Crypto news fetched successfully")
                    return message
            else:
                logger.warning(f"⚠️ Crypto API returned status: {resp.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching crypto news: {e}")
        
        # Fallback message
        return (f"🚀 **Crypto News Update** 🚀\n\n"
                f"**Latest Market News**\n\n"
                f"Stay tuned for real-time cryptocurrency market updates and analysis!\n\n"
                f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    async def fetch_sports_news(self):
        """Fetch real sports news using NewsAPI"""
        if not NEWS_API_KEY:
            logger.warning("⚠️ NewsAPI key not configured")
            return (f"⚽ **Sports News Update** ⚽\n\n"
                    f"**Latest Sports News**\n\n"
                    f"Configure NEWS_API_KEY for live sports updates!\n\n"
                    f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&pageSize=1&apiKey={NEWS_API_KEY}"
        try:
            logger.info("📡 Fetching sports news...")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "articles" in data and len(data["articles"]) > 0:
                    article = data["articles"][0]
                    title = article.get("title", "Latest Sports News").strip()
                    desc = article.get("description", "Stay tuned for updates!").strip()
                    link = article.get("url", "")
                    
                    # Clean and format
                    if len(desc) > 300:
                        desc = desc[:300] + "..."
                    
                    message = f"⚽ **Sports News Update** ⚽\n\n"
                    message += f"**{title}**\n\n"
                    message += f"{desc}\n\n"
                    
                    if link:
                        message += f"[📖 Read Full Article]({link})\n\n"
                    
                    message += f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    
                    logger.info("✅ Sports news fetched successfully")
                    return message
            else:
                logger.warning(f"⚠️ Sports API returned status: {resp.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching sports news: {e}")
        
        # Fallback message
        return (f"⚽ **Sports News Update** ⚽\n\n"
                f"**Latest Sports Headlines**\n\n"
                f"Stay tuned for breaking sports news and updates!\n\n"
                f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # -------------------- Posting Methods --------------------
    async def post_crypto_news(self):
        """Post crypto news to all groups"""
        logger.info("🟡 Starting crypto news post...")
        message = await self.fetch_crypto_news()
        await self._send_to_all_groups(message, "crypto")

    async def post_sports_news(self):
        """Post sports news to all groups"""
        logger.info("🟡 Starting sports news post...")
        message = await self.fetch_sports_news()
        await self._send_to_all_groups(message, "sports")

    async def _send_to_all_groups(self, message, news_type):
        """Send message to all groups with detailed logging"""
        success_count = 0
        total_groups = len(self.group_ids)
        
        logger.info(f"📤 Sending {news_type} news to {total_groups} groups...")
        
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(
                    chat_id=group_id,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                success_count += 1
                logger.info(f"   ✅ Sent to group {group_id}")
                await asyncio.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"   ❌ Failed to send to {group_id}: {str(e)}")
        
        logger.info(f"📊 {news_type.upper()} DELIVERY: {success_count}/{total_groups} successful")

    # -------------------- Scheduler --------------------
    async def start_scheduler(self):
        """Async scheduler that runs news posting at intervals"""
        logger.info(f"⏰ Starting scheduler - Crypto: every {CRYPTO_INTERVAL}min, Sports: every {SPORTS_INTERVAL}min")
        
        last_crypto = 0
        last_sports = 0
        
        while self.running:
            current_time = time.time()
            
            # Crypto news scheduler
            if current_time - last_crypto >= CRYPTO_INTERVAL * 60:
                await self.post_crypto_news()
                last_crypto = current_time
            
            # Sports news scheduler  
            if current_time - last_sports >= SPORTS_INTERVAL * 60:
                await self.post_sports_news()
                last_sports = current_time
            
            # Wait 30 seconds before checking again
            await asyncio.sleep(30)

    async def stop(self):
        """Stop the bot"""
        self.running = False

# -------------------- Main --------------------
async def main():
    logger.info("🤖 Starting Telegram News Bot...")
    
    # Validate configuration
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables")
        return
        
    if not GROUP_IDS:
        logger.error("❌ No GROUP_IDS configured")
        return

    # Initialize bot
    bot = NewsBot(BOT_TOKEN)
    
    # Test bot connection
    if not await bot.test_bot():
        logger.error("❌ Bot initialization failed")
        return
    
    # Test group access
    await bot.test_group_access()
    
    # Send welcome message
    logger.info("📨 Sending welcome messages...")
    welcome_msg = (
        "🤖 **News Bot Activated** 🤖\n\n"
        "I will automatically post:\n"
        f"• 🚀 Crypto news every {CRYPTO_INTERVAL} minutes\n"
        f"• ⚽ Sports news every {SPORTS_INTERVAL} minutes\n\n"
        "Stay tuned for the latest updates!"
    )
    
    await bot._send_to_all_groups(welcome_msg, "welcome")
    
    # Start the scheduler
    logger.info("✅ Bot is now running and will post news automatically!")
    await bot.start_scheduler()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
