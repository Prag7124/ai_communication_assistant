import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import ssl
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SlackSmartSearch:
    def __init__(self, slack_token, ssl_context=None):
        self.client = WebClient(token=slack_token, ssl=ssl_context)

    def search_messages(self, channel_id, query, count=20):
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

    # Initialize the smart search
    smart_searcher = SlackSmartSearch(slack_token, ssl_context=ssl_context)

    # Search for messages in a specific channel with a query
    channel_id = 'YOUR_CHANNEL_ID'
    query = 'task'
    messages = smart_searcher.search_messages(channel_id, query)
    search_results = smart_searcher.format_search_results(messages)
    print("Search Results:\n", search_results)
