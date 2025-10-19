import os
import time
import asyncio
import logging
import requests
import hashlib
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

# -------------------- News Bot with Image Support --------------------
class NewsBot:
    def __init__(self, token):
        self.bot = Bot(token=token)
        self.group_ids = [int(gid.strip()) for gid in GROUP_IDS if gid.strip()]
        self.running = True
        
        # Track posted news to avoid duplicates
        self.posted_crypto_news = set()
        self.posted_sports_news = set()
        
        # Image URLs for different categories
        self.images = {
            'crypto': [
                "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800",
                "https://images.unsplash.com/photo-1621761191311-9c2d46c7429e?w=800",
                "https://images.unsplash.com/photo-1516245834210-c4c142787335?w=800"
            ],
            'sports': [
                "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800",
                "https://images.unsplash.com/photo-1575361204480-aadea25e6e68?w=800",
                "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=800"
            ]
        }
        
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

    def get_image_url(self, category):
        """Get a random image URL for the category"""
        import random
        images = self.images.get(category, [])
        if images:
            return random.choice(images)
        return None

    def create_news_hash(self, title, description):
        """Create hash to identify unique news"""
        content = f"{title}_{description}"[:100]  # Use first 100 chars
        return hashlib.md5(content.encode()).hexdigest()

    # -------------------- Enhanced News Fetchers --------------------
    async def fetch_crypto_news(self):
        """Fetch crypto news and check for duplicates"""
        url = "https://api.coingecko.com/api/v3/news"
        try:
            logger.info("📡 Fetching crypto news...")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and "data" in data and len(data["data"]) > 0:
                    
                    # Find first non-duplicate news
                    for article in data["data"]:
                        title = article.get("title", "").strip()
                        desc = article.get("description", "").strip()
                        
                        if not title or not desc:
                            continue
                            
                        news_hash = self.create_news_hash(title, desc)
                        
                        # Skip if already posted
                        if news_hash in self.posted_crypto_news:
                            logger.info("🔄 Skipping duplicate crypto news")
                            continue
                            
                        # Add to posted set and return
                        self.posted_crypto_news.add(news_hash)
                        
                        # Keep only last 20 news to prevent memory growth
                        if len(self.posted_crypto_news) > 20:
                            self.posted_crypto_news = set(list(self.posted_crypto_news)[-20:])
                        
                        # Clean and format message
                        if len(desc) > 250:
                            desc = desc[:250] + "..."
                        
                        link = article.get("url", "")
                        image_url = article.get("thumb_2x", self.get_image_url('crypto'))
                        
                        message = f"🚀 **Crypto News Update** 🚀\n\n"
                        message += f"**{title}**\n\n"
                        message += f"{desc}\n\n"
                        
                        if link:
                            message += f"[📖 Read Full Article]({link})\n\n"
                        
                        message += f"🕒 {datetime.now().strftime('%H:%M:%S')}"
                        
                        logger.info(f"✅ New crypto news: {title[:50]}...")
                        return message, image_url
                    
                    # If all news are duplicates, return None
                    logger.info("📭 No new crypto news found")
                    return None, None
                    
            else:
                logger.warning(f"⚠️ Crypto API returned status: {resp.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching crypto news: {e}")
        
        return None, None

    async def fetch_sports_news(self):
        """Fetch sports news and check for duplicates"""
        if not NEWS_API_KEY:
            logger.warning("⚠️ NewsAPI key not configured")
            return None, None

        url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&pageSize=5&apiKey={NEWS_API_KEY}"
        try:
            logger.info("📡 Fetching sports news...")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "articles" in data and len(data["articles"]) > 0:
                    
                    # Find first non-duplicate news
                    for article in data["articles"]:
                        title = article.get("title", "").strip()
                        desc = article.get("description", "").strip()
                        
                        if not title or not desc or desc == "[Removed]":
                            continue
                            
                        news_hash = self.create_news_hash(title, desc)
                        
                        # Skip if already posted
                        if news_hash in self.posted_sports_news:
                            logger.info("🔄 Skipping duplicate sports news")
                            continue
                            
                        # Add to posted set and return
                        self.posted_sports_news.add(news_hash)
                        
                        # Keep only last 20 news
                        if len(self.posted_sports_news) > 20:
                            self.posted_sports_news = set(list(self.posted_sports_news)[-20:])
                        
                        # Clean and format
                        if len(desc) > 250:
                            desc = desc[:250] + "..."
                        
                        link = article.get("url", "")
                        image_url = article.get("urlToImage", self.get_image_url('sports'))
                        
                        message = f"⚽ **Sports News Update** ⚽\n\n"
                        message += f"**{title}**\n\n"
                        message += f"{desc}\n\n"
                        
                        if link:
                            message += f"[📖 Read Full Article]({link})\n\n"
                        
                        message += f"🕒 {datetime.now().strftime('%H:%M:%S')}"
                        
                        logger.info(f"✅ New sports news: {title[:50]}...")
                        return message, image_url
                    
                    logger.info("📭 No new sports news found")
                    return None, None
                    
            else:
                logger.warning(f"⚠️ Sports API returned status: {resp.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching sports news: {e}")
        
        return None, None

    # -------------------- Enhanced Posting with Images --------------------
    async def post_crypto_news(self):
        """Post crypto news with image"""
        logger.info("🟡 Starting crypto news post...")
        message, image_url = await self.fetch_crypto_news()
        
        if message:
            await self._send_to_all_groups(message, "crypto", image_url)
        else:
            # Fallback message with image
            fallback_msg = (
                f"🚀 **Crypto Market Update** 🚀\n\n"
                f"**Latest cryptocurrency news and analysis**\n\n"
                f"Stay tuned for real-time market updates and breaking crypto news!\n\n"
                f"🕒 {datetime.now().strftime('%H:%M:%S')}"
            )
            fallback_image = self.get_image_url('crypto')
            await self._send_to_all_groups(fallback_msg, "crypto", fallback_image)

    async def post_sports_news(self):
        """Post sports news with image"""
        logger.info("🟡 Starting sports news post...")
        message, image_url = await self.fetch_sports_news()
        
        if message:
            await self._send_to_all_groups(message, "sports", image_url)
        else:
            # Fallback message with image
            fallback_msg = (
                f"⚽ **Sports News Update** ⚽\n\n"
                f"**Latest sports headlines and updates**\n\n"
                f"Stay tuned for breaking sports news and live updates!\n\n"
                f"🕒 {datetime.now().strftime('%H:%M:%S')}"
            )
            fallback_image = self.get_image_url('sports')
            await self._send_to_all_groups(fallback_msg, "sports", fallback_image)

    async def _send_to_all_groups(self, message, news_type, image_url=None):
        """Send message to all groups with optional image"""
        success_count = 0
        total_groups = len(self.group_ids)
        
        logger.info(f"📤 Sending {news_type} news to {total_groups} groups...")
        
        for group_id in self.group_ids:
            try:
                if image_url:
                    # Send photo with caption
                    await self.bot.send_photo(
                        chat_id=group_id,
                        photo=image_url,
                        caption=message,
                        parse_mode="Markdown"
                    )
                else:
                    # Send text only
                    await self.bot.send_message(
                        chat_id=group_id,
                        text=message,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                
                success_count += 1
                logger.info(f"   ✅ Sent to group {group_id}")
                await asyncio.sleep(1)  # Reduced rate limiting for faster posting
                
            except Exception as e:
                logger.error(f"   ❌ Failed to send to {group_id}: {str(e)}")
                # Try without image if image failed
                if image_url:
                    try:
                        await self.bot.send_message(
                            chat_id=group_id,
                            text=message,
                            parse_mode="Markdown",
                            disable_web_page_preview=True
                        )
                        success_count += 1
                        logger.info(f"   ✅ Sent text-only to group {group_id}")
                    except Exception as e2:
                        logger.error(f"   ❌ Text-only also failed: {str(e2)}")
        
        logger.info(f"📊 {news_type.upper()} DELIVERY: {success_count}/{total_groups} successful")

    # -------------------- Fast Scheduler (1-minute intervals) --------------------
    async def start_scheduler(self):
        """Fast scheduler for 1-minute intervals"""
        logger.info(f"⏰ Starting FAST scheduler")
        logger.info(f"• Crypto: every {CRYPTO_INTERVAL} minutes")
        logger.info(f"• Sports: every {SPORTS_INTERVAL} minutes")
        
        last_crypto = 0
        last_sports = 0
        
        # Initial posts
        await self.post_crypto_news()
        await asyncio.sleep(10)
        await self.post_sports_news()
        
        while self.running:
            current_time = time.time()
            
            # Crypto news scheduler (every CRYPTO_INTERVAL minutes)
            if current_time - last_crypto >= CRYPTO_INTERVAL * 60:
                await self.post_crypto_news()
                last_crypto = current_time
            
            # Sports news scheduler (every SPORTS_INTERVAL minutes)  
            if current_time - last_sports >= SPORTS_INTERVAL * 60:
                await self.post_sports_news()
                last_sports = current_time
            
            # Wait 30 seconds before checking again (faster checking)
            await asyncio.sleep(30)

    async def stop(self):
        """Stop the bot"""
        self.running = False

# -------------------- Main --------------------
async def main():
    logger.info("🤖 Starting Enhanced Telegram News Bot...")
    
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
    
    # Send welcome message
    welcome_msg = (
        "🤖 **Enhanced News Bot Activated** 🤖\n\n"
        "I will automatically post with images:\n"
        f"• 🚀 Crypto news every {CRYPTO_INTERVAL} minutes\n"
        f"• ⚽ Sports news every {SPORTS_INTERVAL} minutes\n\n"
        "✅ No duplicate news\n"
        "🖼️ With engaging images\n"
        "⚡ Fast updates\n\n"
        "Stay tuned for the latest updates!"
    )
    
    await bot._send_to_all_groups(welcome_msg, "welcome", bot.get_image_url('crypto'))
    
    # Start the scheduler
    logger.info("✅ Bot is now running with fast updates!")
    await bot.start_scheduler()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
