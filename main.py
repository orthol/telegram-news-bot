import time
import logging
import requests
from telegram import Bot
from telegram.error import TelegramError
import schedule
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
        
    def send_to_groups(self, message, parse_mode='HTML'):
        """Send message to all groups"""
        success_count = 0
        for group_id in self.group_ids:
            try:
                self.bot.send_message(
                    chat_id=group_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=False
                )
                success_count += 1
                logger.info(f"Message sent to group {group_id}")
                time.sleep(1)  # Rate limiting
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
                    
                    description = news_item.get('description', 'N/A')
                    if len(description) > 300:
                        description = description[:300] + "..."
                    message += f"<b>Description:</b> {description}\n"
                    
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
            url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&apiKey={NEWS_API_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'articles' in data and len(data['articles']) > 0:
                    # Find first article with title and description
                    for article in data['articles']:
                        if article.get('title') and article.get('description'):
                            message = f"⚽ <b>Sports News Update</b> ⚽\n\n"
                            message += f"<b>Title:</b> {article.get('title', 'N/A')}\n"
                            
                            description = article.get('description', '')[:300]
                            if len(description) > 300:
                                description = description[:300] + "..."
                            message += f"<b>Description:</b> {description}\n"
                            
                            if article.get('url'):
                                message += f"\n📖 <a href='{article['url']}'>Read Full Article</a>"
                            
                            message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                            return message
            
            # Fallback if no good articles found
            return "⚽ <b>Sports News Update</b> ⚽\n\nLatest sports news will be updated shortly. Stay tuned!\n\n⏰ " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " UTC"
                
        except Exception as e:
            logger.error(f"Error fetching sports news: {e}")
        
        # Fallback message
        return "⚽ <b>Sports News Update</b> ⚽\n\nWe're currently updating our sports news feed. Check back soon for the latest updates!\n\n⏰ " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " UTC"

    def post_crypto_news(self):
        """Post crypto news to all groups"""
        logger.info("Posting crypto news...")
        news_message = self.get_crypto_news()
        if news_message:
            success_count = self.send_to_groups(news_message)
            logger.info(f"Crypto news posted to {success_count}/{len(self.group_ids)} groups")
        else:
            logger.warning("No crypto news to post")

    def post_sports_news(self):
        """Post sports news to all groups"""
        logger.info("Posting sports news...")
        news_message = self.get_sports_news()
        success_count = self.send_to_groups(news_message)
        logger.info(f"Sports news posted to {success_count}/{len(self.group_ids)} groups")

def main():
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
    schedule.every(CRYPTO_INTERVAL).minutes.do(news_bot.post_crypto_news)
    schedule.every(SPORTS_INTERVAL).minutes.do(news_bot.post_sports_news)

    # Initial post
    news_bot.post_crypto_news()
    news_bot.post_sports_news()

    # Keep the bot running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
