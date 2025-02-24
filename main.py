import logging
from gmail_module.gmail_functions import GmailPriorityManager
from slack_module.summarize import SlackSummarizer
from slack_module.daily_digest import SlackDailyDigest
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os
import ssl
import certifi
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Set SSL context to use certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

def handle_email_response(gmail_manager, message_id):
    """Handle email processing and response."""
    try:
        # Process the email
        result = gmail_manager.process_new_email(message_id)
        
        # Get email data and thread summary
        email_data = result['email_data']
        thread_summary = result['thread_summary']
        
        # Log email details
        logging.info(f"Thread ID: {email_data['thread_id']}")
        logging.info(f"Priority: {result['priority']}")
        logging.info(f"Subject: {thread_summary['subject']}")
        logging.info(f"Summary: {thread_summary['summary']}")
        
        # Suggest quick responses
        response_suggestions = gmail_manager.suggest_responses(email_data)
        print("\nResponse Suggestions:")
        for i, suggestion in enumerate(response_suggestions):
            print(f"{i + 1}. [{suggestion['type']}] {suggestion['text']}")
        
        # Ask user if they want to send a suggested response
        send_response = input("\nDo you want to send a suggested response? (y/n): ").lower()
        if send_response == 'y':
            while True:
                try:
                    choice = int(input(f"\nSelect response option (1-{len(response_suggestions)}): "))
                    if 1 <= choice <= len(response_suggestions):
                        selected_response = response_suggestions[choice - 1]
                        sent_message = gmail_manager.send_quick_response(email_data, selected_response['text'])
                        print(f"Response sent: {selected_response['type'].replace('_', ' ').title()}")
                        break
                    else:
                        print(f"Invalid selection. Please select a number between 1 and {len(response_suggestions)}.")
                except ValueError:
                    print("Please enter a number.")
        
        # Ask user if they want to flag the email for a reminder
        flag_reminder = input("\nDo you want to flag this email for a reminder? (y/n): ").lower()
        if flag_reminder == 'y':
            while True:
                try:
                    print("\nReminder Options:")
                    print("1. Default Reminder (5 hours later)")
                    print("2. Custom Reminder (Set hours)")
                    print("3. Custom Reminder (Set date & time)")
                    reminder_choice = int(input("\nSelect reminder option (1-3): "))
                    
                    if reminder_choice == 1:
                        reminder_time = datetime.now(timezone.utc) + timedelta(hours=5)
                        gmail_manager.flag_email_for_reminder(email_data, reminder_time.isoformat(), "default")
                        print(f"Email flagged for reminder at {reminder_time}.")
                        break
                    
                    elif reminder_choice == 2:
                        hours = float(input("Remind again after how many hours? "))
                        reminder_time = datetime.now(timezone.utc) + timedelta(hours=hours)
                        gmail_manager.flag_email_for_reminder(email_data, reminder_time.isoformat(), "custom")
                        print(f"Email flagged for reminder at {reminder_time}.")
                        break
                    
                    elif reminder_choice == 3:
                        date_str = input("Enter date (YYYY-MM-DD): ")
                        time_str = input("Enter time (HH:MM): ")
                        custom_datetime_str = f"{date_str} {time_str}"
                        reminder_time = datetime.strptime(custom_datetime_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                        gmail_manager.flag_email_for_reminder(email_data, reminder_time.isoformat(), "custom")
                        print(f"Email flagged for reminder at {reminder_time}.")
                        break
                    
                    else:
                        print("Invalid selection. Please select a number between 1 and 3.")
                except ValueError:
                    print("Please enter a valid number.")
    
    except Exception as e:
        logging.error(f"Error handling email response: {str(e)}")
        raise

def gmail_menu(gmail_manager):
    while True:
        print("\n===== Gmail Menu =====")
        print("1. Check Priority Inbox")
        print("2. Summarize Recent Threads")
        print("3. Check Reminders")
        print("4. Back to Main Menu")

        choice = input("\nSelect an option (1-4): ")

        if choice == '1':
            # Get recent messages
            try:
                results = gmail_manager.service.users().messages().list(userId='me', maxResults=10).execute()
                messages = results.get('messages', [])
                
                if not messages:
                    print("No recent messages found.")
                else:
                    print("\n----- Priority Inbox -----")
                    for message in messages:
                        try:
                            result = gmail_manager.process_new_email(message['id'])
                            print(f"Subject: {result['thread_summary']['subject']}")
                            print(f"Priority: {result['priority']}")
                            print(f"Summary: {result['thread_summary']['summary'][:100]}...")
                            print("--------------------------")
                            
                            # Handle email response
                            handle_email_response(gmail_manager, message['id'])
                        except Exception as e:
                            print(f"Error processing message: {str(e)}")
            except Exception as e:
                logging.error(f"Error fetching messages: {str(e)}")
        
        elif choice == '2':
            # Get recent threads
            try:
                results = gmail_manager.service.users().threads().list(userId='me', maxResults=5).execute()
                threads = results.get('threads', [])
                
                if not threads:
                    print("No recent threads found.")
                else:
                    print("\n----- Recent Thread Summaries -----")
                    for thread in threads:
                        try:
                            summary = gmail_manager.summarize_thread(thread['id'])
                            print(f"Subject: {summary['subject']}")
                            print(f"Participants: {', '.join(list(summary['participants'])[:3])}")
                            print(f"Message Count: {summary['message_count']}")
                            print(f"Summary: {summary['summary'][:150]}...")
                            print("--------------------------")
                        except Exception as e:
                            print(f"Error summarizing thread: {str(e)}")
            except Exception as e:
                logging.error(f"Error fetching threads: {str(e)}")
        
        elif choice == '3':
            # Check for reminders
            print("\nChecking for email reminders...")
            try:
                gmail_manager.check_reminders()
                print("Reminder check complete.")
            except Exception as e:
                logging.error(f"Error checking reminders: {str(e)}")
        
        elif choice == '4':
            break
        
        else:
            print("Invalid choice. Please select a number between 1 and 4.")

def slack_menu(slack_token, ssl_context):
    slack_summarizer = SlackSummarizer(slack_token, ssl_context=ssl_context)
    slack_digest = SlackDailyDigest(slack_token, ssl_context=ssl_context)

    while True:
        print("\n===== Slack Menu =====")
        print("1. Summarize Slack Conversations")
        print("2. Generate Daily Digest")
        print("3. Back to Main Menu")

        choice = input("\nSelect an option (1-3): ")

        if choice == '1':
            channel_id = input("Enter Slack channel ID: ")
            try:
                conversations = slack_summarizer.fetch_conversations(channel_id)
                summary = slack_summarizer.summarize_conversation(conversations)
                print("Slack Conversation Summary:", summary)
            except SlackApiError as e:
                logging.error(f"Slack API Error: {e.response['error']}")
            except Exception as e:
                logging.error(f"Error summarizing Slack conversations: {str(e)}")

        elif choice == '2':
            channel_id = input("Enter Slack channel ID: ")
            try:
                conversations = slack_digest.fetch_daily_conversations(channel_id)
                daily_digest = slack_digest.generate_daily_digest(conversations)
                print("Daily Digest:\n", daily_digest)
                send_digest = input("\nDo you want to send this daily digest to the channel? (y/n): ").lower()
                if send_digest == 'y':
                    slack_digest.send_daily_digest(channel_id, daily_digest)
                    print("Daily digest sent.")
            except SlackApiError as e:
                logging.error(f"Slack API Error: {e.response['error']}")
            except Exception as e:
                logging.error(f"Error generating daily digest: {str(e)}")

        elif choice == '3':
            break
        
        else:
            print("Invalid choice. Please select a number between 1 and 3.")

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize the Gmail Priority Manager
    try:
        gmail_manager = GmailPriorityManager()
        print("Authentication successful! AI_Communication_Assistant initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize Gmail Priority Manager: {str(e)}")
        return

    # Access the Slack token
    slack_token = os.getenv('SLACK_TOKEN')
    if not slack_token:
        logging.error("SLACK_TOKEN environment variable not set.")
        return

    # Display main menu for user interaction
    while True:
        print("\n===== AI_Communication_Assistant =====")
        print("1. Gmail")
        print("2. Slack")
        print("3. Exit")

        choice = input("\nSelect an option (1-3): ")
        
        if choice == '1':
            gmail_menu(gmail_manager)
        
        elif choice == '2':
            slack_menu(slack_token, ssl_context)
        
        elif choice == '3':
            print("Exiting AI_Communication_Assistant. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please select a number between 1 and 3.")

if __name__ == "__main__":
    main()
