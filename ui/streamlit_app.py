import streamlit as st
import logging
from dotenv import load_dotenv
import os
import ssl
import sys
from datetime import datetime, timedelta, timezone
import certifi  # import certifi module

# Add the parent directory to the Python path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gmail_module.gmail_functions import GmailPriorityManager
from slack_module.summarize import SlackSummarizer
from slack_module.daily_digest import SlackDailyDigest
from slack_module.message_to_task import SlackMessageToTask
from slack_module.smart_search import SlackSmartSearch
from slack_sdk.errors import SlackApiError

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

def main():
    st.title("AI Communication Assistant")

    menu = ["Home", "Gmail", "Slack"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Home":
        st.subheader("Home")
        st.write("Welcome to the AI Communication Assistant. Please select an option from the sidebar.")

    elif choice == "Gmail":
        st.subheader("Gmail Operations")
        gmail_menu()

    elif choice == "Slack":
        st.subheader("Slack Operations")
        slack_menu()

def gmail_menu():
    gmail_manager = GmailPriorityManager()

    gmail_operations = ["List Emails & Options", "Check Reminders", "Back to Main Menu"]
    operation = st.selectbox("Select Gmail Operation", gmail_operations)

    if operation == "List Emails & Options":
        list_emails_and_options(gmail_manager)
    elif operation == "Check Reminders":
        check_reminders(gmail_manager)
    elif operation == "Back to Main Menu":
        st.experimental_rerun()  # Rerun the app to go back to the main menu

def list_emails_and_options(gmail_manager):
    st.write("Listing Emails with Options...")
    results = gmail_manager.service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])
    
    if not messages:
        st.write("No recent messages found.")
    else:
        for idx, message in enumerate(messages):
            result = gmail_manager.process_new_email(message['id'])
            thread_summary = result['thread_summary']
            st.write(f"Priority: {result['priority']}")
            st.write(f"Subject: {thread_summary['subject']}")
            st.write(f"Summary: {thread_summary['summary'][:100]}...")
            st.write(f"Participants: {', '.join(list(thread_summary['participants'])[:3])}")
            st.write("---")
            handle_email_response(gmail_manager, message['id'], idx)

def check_reminders(gmail_manager):
    st.write("Checking for email reminders...")
    reminders = gmail_manager.check_reminders()
    if not reminders:
        st.write("No reminders found.")
    else:
        for idx, reminder in enumerate(reminders):
            display_reminder(reminder, idx)

def display_reminder(reminder, idx):
    st.write(f"Reminder set for: {reminder['reminder_time']}")
    st.write(f"Subject: {reminder['subject']}")
    st.write(f"Snippet: {reminder['snippet']}")
    
    if st.button("Read Now (Open Email)", key=f"read_now_{reminder['id']}"):
        st.write("Opening email in a new tab...")
        # Here you would implement the logic to open the email
    
    if st.button("Mark as Read", key=f"mark_as_read_{reminder['id']}"):
        st.write("Marking email as read...")
        # Here you would implement the logic to mark the email as read
    
    if st.button("Remind Later (Default: +5 Hours)", key=f"remind_later_default_{reminder['id']}"):
        new_reminder_time = datetime.now(timezone.utc) + timedelta(hours=5)
        st.write(f"Reminder set for: {new_reminder_time}")
        # Here you would implement the logic to update the reminder time
    
    custom_hours = st.number_input("Set custom hours:", min_value=1, max_value=24, step=1, key=f"custom_hours_{reminder['id']}")
    if st.button("Remind Later (Custom Hours)", key=f"remind_later_custom_hours_{reminder['id']}"):
        new_reminder_time = datetime.now(timezone.utc) + timedelta(hours=custom_hours)
        st.write(f"Reminder set for: {new_reminder_time}")
        # Here you would implement the logic to update the reminder time
    
    custom_date = st.date_input("Set custom date:", key=f"custom_date_{reminder['id']}")
    custom_time = st.time_input("Set custom time:", key=f"custom_time_{reminder['id']}")
    if st.button("Remind Later (Custom Date & Time)", key=f"remind_later_custom_datetime_{reminder['id']}"):
        new_reminder_time = datetime.combine(custom_date, custom_time).replace(tzinfo=timezone.utc)
        st.write(f"Reminder set for: {new_reminder_time}")
        # Here you would implement the logic to update the reminder time

def handle_email_response(gmail_manager, message_id, idx):
    result = gmail_manager.process_new_email(message_id)
    email_data = result['email_data']
    response_suggestions = gmail_manager.suggest_responses(email_data)

    if response_suggestions:
        st.write("\nResponse Suggestions:")
        for i, suggestion in enumerate(response_suggestions):
            st.write(f"{i + 1}. [{suggestion['type']}] {suggestion['text']}")
        
        if st.button("Send Suggested Response", key=f"send_response_{idx}"):
            selected_response = st.selectbox("Select Response", [s['text'] for s in response_suggestions], key=f"select_response_{idx}")
            sent_message = gmail_manager.send_quick_response(email_data, selected_response)
            st.write(f"Response sent: {selected_response}")

        if st.button("Flag for Reminder", key=f"flag_reminder_{idx}"):
            reminder_time = st.slider("Set Reminder Time (hours later)", 1, 24, 5, key=f"slider_{idx}")
            reminder_time = datetime.now(timezone.utc) + timedelta(hours=reminder_time)
            gmail_manager.flag_email_for_reminder(email_data, reminder_time.isoformat(), "custom")
            st.write(f"Email flagged for reminder at {reminder_time}.")

def slack_menu():
    bot_token = os.getenv('SLACK_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')

    slack_operations = ["Summarize Slack Conversations", "Generate Daily Digest", "Convert Messages to Tasks", "Smart Search & Retrieval", "Back to Main Menu"]
    operation = st.selectbox("Select Slack Operation", slack_operations)

    if operation == "Back to Main Menu":
        st.experimental_rerun()  # Rerun the app to go back to the main menu

    channel_id = st.text_input("Enter Slack Channel ID")

    if operation == "Summarize Slack Conversations":
        summarize_slack_conversations(bot_token, channel_id)
    elif operation == "Generate Daily Digest":
        generate_daily_digest(bot_token, channel_id)
    elif operation == "Convert Messages to Tasks":
        convert_messages_to_tasks(bot_token, channel_id)
    elif operation == "Smart Search & Retrieval":
        query = st.text_input("Enter Search Query")
        smart_search_retrieval(user_token, channel_id, query)

def summarize_slack_conversations(bot_token, channel_id):
    slack_summarizer = SlackSummarizer(bot_token, ssl_context=ssl_context)
    try:
        conversations = slack_summarizer.fetch_conversations(channel_id)
        summary = slack_summarizer.summarize_conversation(conversations)
        st.write("Slack Conversation Summary:", summary)
    except SlackApiError as e:
        st.error(f"Slack API Error: {e.response['error']}")
    except Exception as e:
        st.error(f"Error summarizing Slack conversations: {str(e)}")

def generate_daily_digest(bot_token, channel_id):
    slack_digest = SlackDailyDigest(bot_token, ssl_context=ssl_context)
    try:
        conversations = slack_digest.fetch_daily_conversations(channel_id)
        daily_digest = slack_digest.generate_daily_digest(conversations)
        st.write("Daily Digest:\n", daily_digest)
        if st.button("Send Daily Digest"):
            slack_digest.send_daily_digest(channel_id, daily_digest)
            st.write("Daily digest sent.")
    except SlackApiError as e:
        st.error(f"Slack API Error: {e.response['error']}")
    except Exception as e:
        st.error(f"Error generating daily digest: {str(e)}")

def convert_messages_to_tasks(bot_token, channel_id):
    slack_task_converter = SlackMessageToTask(bot_token, ssl_context=ssl_context)
    try:
        tasks = slack_task_converter.extract_tasks(channel_id)
        st.write("Extracted Tasks:", tasks)
    except SlackApiError as e:
        st.error(f"Slack API Error: {e.response['error']}")
    except Exception as e:
        st.error(f"Error extracting tasks: {str(e)}")

def smart_search_retrieval(user_token, channel_id, query):
    slack_smart_searcher = SlackSmartSearch(user_token, ssl_context=ssl_context)
    try:
        messages = slack_smart_searcher.search_messages(query)
        search_results = slack_smart_searcher.format_search_results(messages)
        st.write("Search Results:\n", search_results)
    except SlackApiError as e:
        st.error(f"Slack API Error: {e.response['error']}")
    except Exception as e:
        st.error(f"Error performing smart search: {str(e)}")

if __name__ == "__main__":
    main()
