import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import ssl
import certifi
from .summarize import summarize_conversation
from .daily_digest import SlackDailyDigest
from .message_to_task import SlackMessageToTask
from .smart_search import SlackSmartSearch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SlackManager:
    def __init__(self, slack_token, ssl_context=None):
        self.client = WebClient(token=slack_token, ssl=ssl_context)
        self.daily_digest = SlackDailyDigest(slack_token, ssl_context)
        self.message_to_task = SlackMessageToTask(slack_token, ssl_context)
        self.smart_search = SlackSmartSearch(slack_token, ssl_context)

    def get_conversations(self, channel_id):
        try:
            result = self.client.conversations_history(channel=channel_id)
            conversations = result['messages']
            return conversations
        except SlackApiError as e:
            logging.error(f"Error fetching conversations: {e.response['error']}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return []

    def generate_daily_digest(self, channel_id):
        return self.daily_digest.generate_daily_digest(channel_id)

    def convert_message_to_task(self, message):
        return self.message_to_task.convert_message_to_task(message)

    def search_messages(self, query):
        return self.smart_search.search_messages(query)
