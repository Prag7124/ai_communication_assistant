import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import ssl
import certifi
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SlackMessageToTask:
    def __init__(self, slack_token, ssl_context=None):
        self.client = WebClient(token=slack_token, ssl=ssl_context)

    def fetch_messages(self, channel_id, days=1):
        try:
            now = datetime.now()
            oldest = (now - timedelta(days=days)).timestamp()
            result = self.client.conversations_history(channel=channel_id, oldest=oldest)
            messages = result['messages']
            return messages
        except SlackApiError as e:
            logging.error(f"Error fetching messages: {e.response['error']}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return []

    def convert_message_to_task(self, message):
        try:
            # For simplicity, assume that messages containing the word "task" are tasks
            if 'task' in message['text'].lower():
                task = {
                    'user': message.get('user', 'Unknown'),
                    'text': message.get('text', ''),
                    'timestamp': datetime.fromtimestamp(float(message['ts'])).strftime('%Y-%m-%d %H:%M:%S')
                }
                return task
            return None
        except Exception as e:
            logging.error(f"Error converting message to task: {str(e)}")
            return None

    def extract_tasks(self, channel_id, days=1):
        tasks = []
        messages = self.fetch_messages(channel_id, days)
        for message in messages:
            task = self.convert_message_to_task(message)
            if task:
                tasks.append(task)
        return tasks

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

    # Initialize the message to task converter
    task_converter = SlackMessageToTask(slack_token, ssl_context=ssl_context)

    # Fetch and extract tasks from a specific channel
    channel_id = 'YOUR_CHANNEL_ID'
    tasks = task_converter.extract_tasks(channel_id)
    print("Extracted Tasks:", tasks)
