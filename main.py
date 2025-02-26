import logging
from gmail_module.gmail_functions import GmailPriorityManager
from slack_module.summarize import SlackSummarizer
from slack_module.daily_digest import SlackDailyDigest
from slack_module.message_to_task import SlackMessageToTask
from slack_module.smart_search import SlackSmartSearch
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
                    reminder_choice = int(input("\nSelect reminder option (1-2): "))
                    
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
                    
                    else:
                        print("Invalid selection. Please select a number between 1 and 2.")
                except ValueError:
                    print("Please enter a valid number.")
    
    except Exception as e:
        logging.error(f"Error handling email response: {str(e)}")
        raise

def gmail_menu(gmail_manager):
    while True:
        print("\n===== Gmail Menu =====")
        print("1. Check Priority Inbox")
        print("2. Check Reminders")
        print("3. Back to Main Menu")

        choice = input("\nSelect an option (1-3): ")

        if choice == '1':
            # Get recent messages
            try:
                results = gmail_manager.service.users().messages().list(userId='me', maxResults=10).execute()
                messages = results.get('messages', [])
                
                if not messages:
                    print("No recent messages found.")
                else:
                    for i, message in enumerate(messages):
                        try:
                            result = gmail_manager.process_new_email(message['id'])
                            print(f"\nEmail {i + 1}")
                            print(f"Subject: {result['thread_summary']['subject']}")
                            print(f"Priority: {result['priority']}")
                            print(f"Summary: {result['thread_summary']['summary'][:100]}...")
                            print("--------------------------")
                            
                            # Handle email response
                            handle_email_response(gmail_manager, message['id'])
                            
                            # Option to show next email or go back to menu
                            next_action = input("\nEnter 'n' to see the next email or 'b' to go back to menu: ").lower()
                            if next_action == 'b':
                                break
                        except Exception as e:
                            print(f"Error processing message: {str(e)}")
            except Exception as e:
                logging.error(f"Error fetching messages: {str(e)}")
        
        elif choice == '2':
            # Check for reminders
            print("\nChecking for email reminders...")
            try:
                gmail_manager.check_reminders()
                print("Reminder check complete.")
            except Exception as e:
                logging.error(f"Error checking reminders: {str(e)}")
        
        elif choice == '3':
            break
        
        else:
            print("Invalid choice. Please select a number between 1 and 3.")

def slack_menu(bot_token, user_token, ssl_context):
    slack_summarizer = SlackSummarizer(bot_token, ssl_context=ssl_context)
    slack_digest = SlackDailyDigest(bot_token, ssl_context=ssl_context)
    slack_task_converter = SlackMessageToTask(bot_token, ssl_context=ssl_context)
    slack_smart_searcher = SlackSmartSearch(user_token, ssl_context=ssl_context)

    while True:
        print("\n===== Slack Menu =====")
        print("1. Summarize Slack Conversations")
        print("2. Generate Daily Digest")
        print("3. Convert Messages to Tasks")
        print("4. Smart Search & Retrieval")
        print("5. Back to Main Menu")

        choice = input("\nSelect an option (1-5): ")

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
            channel_id = input("Enter Slack channel ID: ")
            try:
                tasks = slack_task_converter.extract_tasks(channel_id)
                if not tasks:
                    print("No tasks found.")
                else:
                    print("Extracted Tasks:", tasks)
            except SlackApiError as e:
                logging.error(f"Slack API Error: {e.response['error']}")
            except Exception as e:
                logging.error(f"Error extracting tasks: {str(e)}")

        elif choice == '4':
            channel_id = input("Enter Slack channel ID: ")
            query = input("Enter search query: ")
            try:
                messages = slack_smart_searcher.search_messages(query)
                search_results = slack_smart_searcher.format_search_results(messages)
                print("Search Results:\n", search_results)
            except SlackApiError as e:
                logging.error(f"Slack API Error: {e.response['error']}")
            except Exception as e:
                logging.error(f"Error performing smart search: {str(e)}")

        elif choice == '5':
            break
        
        else:
            print("Invalid choice. Please select a number between 1 and 5.")

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

    # Access the Slack tokens
    bot_token = os.getenv('SLACK_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    if not bot_token or not user_token:
        logging.error("SLACK_TOKEN or SLACK_USER_TOKEN environment variable not set.")
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
            slack_menu(bot_token, user_token, ssl_context)
        
        elif choice == '3':
            print("Exiting AI_Communication_Assistant. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please select a number between 1 and 3.")

if __name__ == "__main__":
    main()
