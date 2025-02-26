from .api_client import WhatsAppAPIClient
from .smart_reply import generate_smart_reply
from .summarizer import summarize_text

class WhatsAppAssistant:
    def __init__(self, api_client):
        self.api_client = api_client

    def handle_incoming_message(self, data, action):
        message = data['Body']
        from_number = data['From']

        if action == '1':
            response = generate_smart_reply(message)
            self.api_client.send_message(from_number, response)
        elif action == '2':
            summary = self.summarize_conversation(message)
            self.api_client.send_message(from_number, summary)
        elif action == '3':
            self.handle_basic_query(message, from_number)
        else:
            response = "Invalid action. Please select a valid option."
            self.api_client.send_message(from_number, response)

    def summarize_conversation(self, conversation):
        summary = summarize_text(conversation)
        return summary
    
    def handle_basic_query(self, query, from_number):
        response = "This is a basic customer service response."
        self.api_client.send_message(from_number, response)
