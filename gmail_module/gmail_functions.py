import os
import base64
import logging
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from transformers import pipeline

# Initialize the sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis")

# Define the scopes for accessing Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.modify', 
          'https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    """Authenticate and return Gmail API credentials."""
    creds = None

    # Check if token.json exists for previously saved credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, log in and save new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def fetch_emails(creds, max_results=10):
    """Fetch a specified number of emails from the user's Gmail account."""
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])

        email_data = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            email_data.append(msg)

        return email_data
    except HttpError as error:
        print(f"❌ Error fetching emails: {error}")
        return []

def send_email(creds, recipient, subject, body):
    """Send an email using the Gmail API."""
    try:
        service = build('gmail', 'v1', credentials=creds)

        # Create the email message
        message = MIMEText(body, "plain", "utf-8")  # Explicit encoding
        message["to"] = recipient
        message["subject"] = subject

        # Encode the message as base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send the email
        sent_message = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        print(f"✅ Email sent successfully to {recipient}. Message ID: {sent_message['id']}")
        return sent_message

    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        return None
def classify_email(subject, body):
    """Classify email based on sentiment."""
    text = f"{subject} {body}"
    sentiment = sentiment_analyzer(text)
    return "Urgent" if sentiment[0]['label'] == 'POSITIVE' else "Low Priority"

