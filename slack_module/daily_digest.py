import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import ssl
import certifi
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SlackDailyDigest:
    def __init__(self, slack_token, ssl_context=None):
        self.client = WebClient(token=slack_token, ssl=ssl_context)

    def fetch_daily_conversations(self, channel_id, days=1):
        try:
            now = datetime.now()
            oldest = (now - timedelta(days=days)).timestamp()
            result = self.client.conversations_history(channel=channel_id, oldest=oldest)
            conversations = result['messages']
            return conversations
        except SlackApiError as e:
            logging.error(f"Error fetching conversations: {e.response['error']}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return []

    def generate_daily_digest(self, conversations):
        digest = []
        for message in conversations:
            timestamp = datetime.fromtimestamp(float(message['ts']))
            user = message.get('user', 'Unknown')
            text = message.get('text', '')
            digest.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {user}: {text}")
        return "\n".join(digest)

    def send_daily_digest(self, channel_id, digest):
        try:
            self.client.chat_postMessage(channel=channel_id, text=digest)
        except SlackApiError as e:
            logging.error(f"Error sending daily digest: {e.response['error']}")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")

# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    # Load environment variables from .env file
    load_dotenv()

    # Access the Slack token
    slack_token = os.getenv('SLACK_TOKEN')

    # Create SSL context
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Initialize the digest generator
    digest_generator = SlackDailyDigest(slack_token, ssl_context=ssl_context)

    # Fetch and generate daily digest for a specific channel
    channel_id = 'YOUR_CHANNEL_ID'
    conversations = digest_generator.fetch_daily_conversations(channel_id)
    daily_digest = digest_generator.generate_daily_digest(conversations)
    print("Daily Digest:\n", daily_digest)

    # Optionally send the daily digest to a channel
    digest_generator.send_daily_digest(channel_id, daily_digest)
