from twilio.rest import Client

class WhatsAppAPIClient:
    def __init__(self, account_sid, auth_token, from_whatsapp_number):
        self.client = Client(account_sid, auth_token)
        self.from_whatsapp_number = from_whatsapp_number

    def send_message(self, to_whatsapp_number, message):
        message = self.client.messages.create(
            body=message,
            from_=f'whatsapp:{self.from_whatsapp_number}',
            to=f'whatsapp:{to_whatsapp_number}'
        )
        return message.sid

    def receive_message(self, data):
        # Logic to handle incoming messages
        pass
