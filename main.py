import logging
from gmail_module.gmail_functions import authenticate_gmail, fetch_emails, send_email

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    """Main function to authenticate, fetch emails, and send an email."""
    logging.info("🔄 Starting Gmail authentication...")

    creds = authenticate_gmail()
    if not creds:
        logging.error("❌ Authentication failed. Exiting program.")
        return

    logging.info("✅ Authentication successful!")

    # Fetch emails (change max_results as needed)
    emails = fetch_emails(creds, max_results=10)

    if not emails:
        logging.warning("⚠️ No emails found.")
    else:
        logging.info(f"📩 Fetched {len(emails)} emails.")
        # Print email subjects
        for idx, email in enumerate(emails, start=1):
            subject = next((header["value"] for header in email["payload"]["headers"] if header["name"] == "Subject"), "No Subject")
            logging.info(f"{idx}. {subject}")

    # Send an email
    recipient = "example@gmail.com"  # Change this to the recipient's email
    subject = "Test Email from Gmail API"
    body = "Hello, this is a test email sent using the Gmail API!"
    
    logging.info(f"📤 Sending email to {recipient}...")
    sent_email = send_email(creds, recipient, subject, body)

    if sent_email:
        logging.info(f"✅ Email sent successfully! Message ID: {sent_email['id']}")
    else:
        logging.error("❌ Failed to send email.")

if __name__ == "__main__":
    main()

