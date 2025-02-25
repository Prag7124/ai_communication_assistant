import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import ssl
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SlackSmartSearch:
    def __init__(self, user_token, ssl_context=None):
        self.client = WebClient(token=user_token, ssl=ssl_context)

    def search_messages(self, query, count=20):
        try:
            result = self.client.search_messages(query=query, count=count, sort='timestamp', sort_dir='desc')
            messages = result['messages']['matches']
            return messages
        except SlackApiError as e:
            logging.error(f"Error searching messages: {e.response['error']}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return []

    def format_search_results(self, messages):
        formatted_results = []
        for message in messages:
            timestamp = message['ts']
            user = message.get('user', 'Unknown')
            text = message.get('text', '')
            formatted_results.append(f"{timestamp} - {user}: {text}")
        return "\n".join(formatted_results)
