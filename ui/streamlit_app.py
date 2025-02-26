import streamlit as st
from gmail_module.gmail_functions import GmailPriorityManager
from slack_module.slack_functions import SlackManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize managers
gmail_manager = GmailPriorityManager()
slack_manager = SlackManager()

st.title('AI Communication Assistant')

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose the app mode", ["Gmail", "Slack"])

if app_mode == "Gmail":
    st.header("Gmail Management")
    if st.button("Load Unread Emails"):
        with st.spinner('Loading unread emails...'):
            try:
                unread_emails = gmail_manager.get_unread_emails()
                st.session_state.unread_emails = unread_emails  # Store in session state
                if unread_emails:
                    st.success(f"Loaded {len(unread_emails)} unread email(s).")
                else:
                    st.info("No unread emails found.")
            except Exception as e:
                st.error(f"Error loading unread emails: {str(e)}")

    if "unread_emails" in st.session_state:
        unread_emails = st.session_state.unread_emails
        for idx, email_info in enumerate(unread_emails):
            email_data = email_info.get('email_data', {})
            thread_summary = email_info.get('thread_summary', {})
            priority = email_info.get('priority', 'Low Priority')

            st.subheader(f"Email {idx + 1}")
            st.write(f"**From:** {email_data.get('sender', 'Unknown Sender')}")
            st.write(f"**Subject:** {email_data.get('subject', 'No Subject')}")
            st.write(f"**Priority:** {priority}")
            st.write(f"**Summary:** {thread_summary.get('summary', 'No summary available')}")
            st.write(f"**Key Points:** {', '.join(thread_summary.get('key_points', []))}")
            st.write(f"**Latest Update:** {thread_summary.get('latest_update', 'No updates')}")

            if st.button(f"Respond to Email {idx + 1}", key=f"respond_{idx}"):
                response_text = st.text_area(f"Enter your response for Email {idx + 1}:", height=200, key=f"response_text_{idx}")
                if st.button(f"Send Response for Email {idx + 1}", key=f"send_response_{idx}"):
                    if response_text.strip():
                        try:
                            gmail_manager.send_quick_response(email_data, response_text)
                            st.success("Response sent successfully!")
                        except Exception as e:
                            st.error(f"Error sending response: {str(e)}")
                    else:
                        st.warning("Response text is empty. Please enter a response.")

    if st.button("Check Reminders"):
        with st.spinner('Checking reminders...'):
            try:
                reminder_count = gmail_manager.check_reminders()
                if reminder_count > 0:
                    st.success(f"Found {reminder_count} reminders.")
                else:
                    st.info("No reminders due at this time.")
            except Exception as e:
                st.error(f"Error checking reminders: {str(e)}")

elif app_mode == "Slack":
    st.header("Slack Management")
    if st.button("Load Slack Conversations"):
        with st.spinner('Loading Slack conversations...'):
            try:
                conversations = slack_manager.get_conversations()
                st.session_state.conversations = conversations  # Store in session state
                if conversations:
                    st.success(f"Loaded {len(conversations)} conversation(s).")
                else:
                    st.info("No conversations found.")
            except Exception as e:
                st.error(f"Error loading Slack conversations: {str(e)}")

    if "conversations" in st.session_state:
        conversations = st.session_state.conversations
        for idx, conv in enumerate(conversations):
            st.subheader(f"Conversation {idx + 1}")
            st.write(f"**Channel:** {conv['channel']}")
            st.write(f"**Participants:** {', '.join(conv['participants'])}")
            st.write(f"**Summary:** {conv['summary']}")

            if st.button(f"Generate Daily Digest for {conv['channel']}", key=f"digest_{idx}"):
                try:
                    digest = slack_manager.generate_daily_digest(conv['channel'])
                    st.write(f"**Daily Digest:** {digest}")
                except Exception as e:
                    st.error(f"Error generating daily digest: {str(e)}")

            if st.button(f"Convert Message to Task for {conv['channel']}", key=f"task_{idx}"):
                message = st.text_area(f"Enter the message to convert to task for {conv['channel']}:", height=100, key=f"task_message_{idx}")
                if st.button(f"Convert Message for {conv['channel']}", key=f"convert_task_{idx}"):
                    if message.strip():
                        try:
                            task = slack_manager.convert_message_to_task(message)
                            st.write(f"**Task Created:** {task}")
                        except Exception as e:
                            st.error(f"Error converting message to task: {str(e)}")
                    else:
                        st.warning("Message text is empty. Please enter a message.")

            if st.button(f"Smart Search in {conv['channel']}", key=f"search_{idx}"):
                query = st.text_input(f"Enter search query for {conv['channel']}:", key=f"search_query_{idx}")
                if st.button(f"Search Messages for {conv['channel']}", key=f"search_messages_{idx}"):
                    if query.strip():
                        try:
                            results = slack_manager.search_messages(query)
                            st.write(f"**Search Results:** {results}")
                        except Exception as e:
                            st.error(f"Error searching messages: {str(e)}")
                    else:
                        st.warning("Search query is empty. Please enter a query.")
