import asyncio
import logging
import requests
from telegram import Bot
from telegram.error import TelegramError
import schedule
import time
from datetime import datetime
from config import *

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NewsBot:
    def __init__(self, token):
        self.bot = Bot(token=token)
        self.group_ids = GROUP_IDS[:MAX_GROUPS]  # Limit to max groups
        
    async def send_to_groups(self, message, parse_mode='HTML'):
        """Send message to all groups"""
        success_count = 0
        for group_id in self.group_ids:
            try:
                await self.bot.send_message(
                    chat_id=group_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=False
                )
                success_count += 1
                logger.info(f"Message sent to group {group_id}")
                await asyncio.sleep(1)  # Rate limiting
            except TelegramError as e:
                logger.error(f"Failed to send to group {group_id}: {e}")
        
        return success_count

    def get_crypto_news(self):
        """Fetch crypto news from CoinGecko API"""
        try:
            response = requests.get(CRYPTO_NEWS_API, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    news_item = data['data'][0]  # Get latest news
                    
                    message = f"🚀 <b>Crypto News Update</b> 🚀\n\n"
                    message += f"<b>Title:</b> {news_item.get('title', 'N/A')}\n"
                    message += f"<b>Description:</b> {news_item.get('description', 'N/A')[:300]}...\n"
                    
                    if news_item.get('url'):
                        message += f"\n📖 <a href='{news_item['url']}'>Read Full Article</a>"
                    
                    message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    return message
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
        
        return None

    def get_sports_news(self):
        """Fetch sports news from NewsAPI"""
        if not NEWS_API_KEY:
            logger.error("NewsAPI key not configured")
            return None
            
        try:
            url = SPORTS_NEWS_API.format(NEWS_API_KEY)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'articles' in data and len(data['articles']) > 0:
                    article = data['articles'][0]  # Get latest article
                    
                    message = f"⚽ <b>Sports News Update</b> ⚽\n\n"
                    message += f"<b>Title:</b> {article.get('title', 'N/A')}\n"
                    
                    if article.get('description'):
                        message += f"<b>Description:</b> {article['description'][:300]}...\n"
                    
                    if article.get('url'):
                        message += f"\n📖 <a href='{article['url']}'>Read Full Article</a>"
                    
                    message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    return message
        except Exception as e:
            logger.error(f"Error fetching sports news: {e}")
        
        return None

    async def post_crypto_news(self):
        """Post crypto news to all groups"""
        logger.info("Posting crypto news...")
        news_message = self.get_crypto_news()
        if news_message:
            success_count = await self.send_to_groups(news_message)
            logger.info(f"Crypto news posted to {success_count}/{len(self.group_ids)} groups")
        else:
            logger.warning("No crypto news to post")

    async def post_sports_news(self):
        """Post sports news to all groups"""
        logger.info("Posting sports news...")
        news_message = self.get_sports_news()
        if news_message:
            success_count = await self.send_to_groups(news_message)
            logger.info(f"Sports news posted to {success_count}/{len(self.group_ids)} groups")
        else:
            # Fallback message if API fails
            fallback_message = (
                f"🏆 <b>Sports News Update</b> 🏆\n\n"
                f"Stay tuned for the latest sports news! "
                f"We're currently updating our news feed.\n\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            await self.send_to_groups(fallback_message)
            logger.info("Fallback sports message sent")

def run_async_job(job_func):
    """Helper to run async functions in schedule"""
    asyncio.run(job_func())

async def main():
    """Main function to initialize and run the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
        
    if not GROUP_IDS:
        logger.error("No GROUP_IDS configured")
        return

    # Initialize bot
    news_bot = NewsBot(BOT_TOKEN)
    
    logger.info(f"News Bot started! Monitoring {len(news_bot.group_ids)} groups")
    logger.info(f"Crypto news interval: {CRYPTO_INTERVAL} minutes")
    logger.info(f"Sports news interval: {SPORTS_INTERVAL} minutes")

    # Schedule news posts
    schedule.every(CRYPTO_INTERVAL).minutes.do(
        lambda: run_async_job(news_bot.post_crypto_news)
    )
    schedule.every(SPORTS_INTERVAL).minutes.do(
        lambda: run_async_job(news_bot.post_sports_news)
    )

    # Initial post
    await asyncio.gather(
        news_bot.post_crypto_news(),
        news_bot.post_sports_news()
    )

    # Keep the bot running
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
