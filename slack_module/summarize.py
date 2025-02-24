import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import spacy
from transformers import pipeline
import ssl
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load NLP models
try:
    nlp = spacy.load("en_core_web_sm")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    logging.error(f"Error loading NLP models: {str(e)}")
    nlp = None
    summarizer = None

class SlackSummarizer:
    def __init__(self, slack_token, ssl_context=None):
        self.client = WebClient(token=slack_token, ssl=ssl_context)

    def fetch_conversations(self, channel_id):
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

    def summarize_conversation(self, conversation):
        try:
            text = " ".join([message['text'] for message in conversation])
            if len(text.split()) < 30:
                return text  # Return the text as is if it's too short for summarization
            max_length = min(120, len(text.split()))
            summary = summarizer(text, max_length=max_length, min_length=30, do_sample=False)[0]['summary_text']
            return summary
        except Exception as e:
            logging.error(f"Error summarizing conversation: {str(e)}")
            return ""

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

    # Initialize the summarizer
    summarizer = SlackSummarizer(slack_token, ssl_context=ssl_context)

    # Fetch and summarize conversations from a specific channel
    channel_id = 'C08EGTBHNE9'
    conversations = summarizer.fetch_conversations(channel_id)
    summary = summarizer.summarize_conversation(conversations)
    print("Summary:", summary)
