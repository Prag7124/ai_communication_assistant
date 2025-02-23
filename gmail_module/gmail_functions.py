import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from transformers import pipeline

# Define the scopes for accessing Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

# Initialize the sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis")
# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def authenticate_gmail():
    """Authenticate and return Gmail API credentials."""
    creds = None

    # Check if token.json exists for previously saved credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no valid credentials available, let the user log in.
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

#def fetch_emails(creds):
#    """Fetch emails from the user's Gmail account."""
#    service = build('gmail', 'v1', credentials=creds)
#    results = service.users().messages().list(userId='me').execute()
#    messages = results.get('messages', [])
    
#    email_data = []
#    for message in messages:
#        msg = service.users().messages().get(userId='me', id=message['id']).execute()
#        email_data.append(msg)
    
#    return email_data


def fetch_email_threads(creds):
    """Fetch email threads from the user's Gmail account."""
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])

    email_threads = {}

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        
        # Get the thread ID of the message
        thread_id = msg['threadId']
        
        # Group emails by thread ID
        if thread_id not in email_threads:
            email_threads[thread_id] = []
        
        # Extract the snippet or full body of the email as needed
        email_body = msg.get('snippet', '')  # This gets a short preview; you may want to fetch the full body.
        email_threads[thread_id].append(email_body)

    return email_threads

def send_email(creds, recipient, subject, body):
    """Send an email using the Gmail API."""
    service = build('gmail', 'v1', credentials=creds)

    # Create the email message
    message = MIMEText(body)
    message['to'] = recipient
    message['subject'] = subject

    # Encode the message as base64
    create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    try:
        # Send the email
        message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"Email sent successfully to {recipient}. Message ID: {message['id']}")
    except Exception as error:
        print(f"An error occurred: {error}")

def classify_email(subject, body):
    """Classify email based on sentiment and keywords."""
    text = f"{subject} {body}"
    sentiment = sentiment_analyzer(text)

    # Define keywords for classification
    urgent_keywords = ["urgent", "asap", "important", "immediate", "action required"]
    follow_up_keywords = ["follow-up", "reminder", "check-in"]
    low_priority_keywords = ["promotional", "newsletter", "free trial", "limited time offer"]

    # Check for urgent keywords
    if any(keyword in text.lower() for keyword in urgent_keywords):
        return "Urgent"
    
    # Check for follow-up keywords
    if any(keyword in text.lower() for keyword in follow_up_keywords):
        return "Follow-up"

    # Check for low priority keywords
    if any(keyword in text.lower() for keyword in low_priority_keywords):
        return "Low Priority"

    # Use sentiment analysis as a fallback
    if sentiment[0]['label'] == 'POSITIVE':
        return "Urgent"
    
    return "Low Priority"  # Default classification if no other conditions are met

def summarize_email_thread(email_bodies):
    """Generate a summary for a list of email bodies."""
    # Join all email bodies into a single string
    full_text = " ".join(email_bodies)

    # Calculate an appropriate max_length based on input length
    input_length = len(full_text.split())
    max_length = min(150, max(30, input_length // 2))  # Set max_length dynamically

    # Generate summary using the summarization model
    summary = summarizer(full_text, max_length=max_length, min_length=30, do_sample=False)

    return summary[0]['summary_text']
    
    

