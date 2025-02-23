import logging
from gmail_module.gmail_functions import authenticate_gmail, fetch_email_threads, classify_email, summarize_email_thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    # Authenticate and get Gmail API credentials
    creds = authenticate_gmail()
    logging.info("Authentication successful!")

    # Fetch email threads from Gmail
    email_threads = fetch_email_threads(creds)
    
    logging.info(f"Fetched {len(email_threads)} email threads.")

    # Classify each email thread based on sentiment and log priority
    for index, (thread_id, email_bodies) in enumerate(email_threads.items()):
        # Generate a summary for the email thread
        summary = summarize_email_thread(email_bodies)
        
        # Classify based on the first email body (or however you want to classify)
        first_subject = email_bodies[0]  # You may want to extract a proper subject from the first email body
        priority = classify_email(first_subject, summary)

        # Log the email thread information in the desired format
        logging.info(f"{index + 1}. [Thread ID: {thread_id}] [{priority}] Summary: {summary}")

if __name__ == "__main__":
    main()

