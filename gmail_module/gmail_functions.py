import os
import json
import pickle
import logging
import base64
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from transformers import pipeline
import spacy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load NLP models
try:
    nlp = spacy.load("en_core_web_sm")
    sentiment_analyzer = pipeline("sentiment-analysis")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    logging.error(f"Error loading NLP models: {str(e)}")
    nlp = None
    sentiment_analyzer = None
    summarizer = None

class ResponseSuggester:
    """Class to generate response suggestions for emails."""
    
    def __init__(self):
        self.common_responses = {
            "acknowledgment": "Thank you for your email. I've received it and will get back to you shortly.",
            "meeting_accept": "I'd be happy to meet with you. The proposed time works for me.",
            "meeting_reject": "Unfortunately, I won't be able to make that time. Could we find an alternative?",
            "more_info": "Thank you for reaching out. Could you provide some additional details so I can better assist you?",
            "follow_up": "I wanted to follow up on our previous conversation. Have you had a chance to review the information I sent?",
        }
    
    def get_suggestions(self, email_content, email_context):
        """Generate response suggestions based on email content and context."""
        suggestions = []
        
        # Basic acknowledgment (always offer this)
        suggestions.append({
            "type": "acknowledgment",
            "text": self.common_responses["acknowledgment"]
        })
        
        # Check for meeting requests
        if any keyword in email_content.lower() for keyword in ["meet", "meeting", "appointment", "schedule", "calendar"]:
            suggestions.append({
                "type": "meeting_accept",
                "text": self.common_responses["meeting_accept"]
            })
            suggestions.append({
                "type": "meeting_reject",
                "text": self.common_responses["meeting_reject"]
            })
        
        # Check for questions or info requests
        if "?" in email_content or any keyword in email_content.lower() for keyword in ["question", "inquiry", "help", "information", "details"]:
            suggestions.append({
                "type": "more_info",
                "text": self.common_responses["more_info"]
            })
        
        # Add custom response based on sender (if we have history)
        sender = email_context.get('sender', '')
        if sender:
            sender_name = sender.split('<')[0].strip()
            custom_response = f"Hi {sender_name}, thanks for your email about '{email_context.get('subject', '')}'. I'll look into this and get back to you as soon as possible."
            suggestions.append({
                "type": "custom_personal",
                "text": custom_response
            })
        
        # Add priority-based response if marked important
        if email_context.get('is_important', False):
            suggestions.append({
                "type": "priority_response",
                "text": "I see this is an important matter. I'm prioritizing it and will address it promptly."
            })
        
        return suggestions

class GmailPriorityManager:
    def __init__(self, credentials_path="credentials.json", token_path="token.pickle",
                 behavior_file="user_behavior.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.behavior_file = behavior_file
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
        self.urgent_keywords = {
            "urgent", "asap", "immediate", "emergency", "deadline", "Due date",
            "important", "priority", "critical", "crucial"
        }
        self.service = None
        # Use a fixed port that must be registered in Google Cloud Console
        self.auth_port = 8080
        self.credentials = None
        self.response_suggester = ResponseSuggester()
        self.reminders = []
        self.initialize_service()

    def initialize_service(self):
        """Initialize Gmail API service with authentication."""
        creds = self._authenticate()
        self.credentials = creds
        self.service = build("gmail", "v1", credentials=creds)

    def _authenticate(self):
        """Handle Gmail API authentication."""
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds valid:
            if creds and creds expired and creds refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=self.auth_port)  # Use fixed port
            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)

        return creds

    def check_importance(self, message):
        """Check if email is marked as important by Gmail."""
        labels = message.get('labelIds', [])
        return 'IMPORTANT' in labels

    def analyze_sender_history(self, sender_email):
        """Analyze sender's email history for prioritization."""
        try:
            if not os.path.exists(self.behavior_file):
                return False

            with open(self.behavior_file, 'r') as f:
                behavior_data = json.load(f)
            sender_stats = behavior_data.get(sender_email, {})
            response_rate = sender_stats.get('response_rate', 0)
            return response_rate > 0.7
        except Exception as e:
            logging.error(f"Error analyzing sender history: {str(e)}")
            return False

    def decode_base64(self, data):
        """Decode base64 email content."""
        try:
            if not data:
                return ""
            return base64.urlsafe_b64decode(data).decode('utf-8')
        except Exception as e:
            logging.error(f"Error decoding content: {str(e)}")
            return ""

    def extract_email_content(self, message):
        """Extract and decode email content."""
        try:
            payload = message['payload']
            headers = {header['name']: header['value']
                      for header in payload.get('headers', [])}

            subject = headers.get('Subject', '')
            sender = headers.get('From', '')
            content = ""

            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        content += self.decode_base64(data)
            else:
                data = payload.get('body', {}).get('data', '')
                content = self.decode_base64(data)

            return subject, sender, content
        except Exception as e:
            logging.error(f"Error extracting email content: {str(e)}")
            return "", "", ""

    def analyze_priority(self, email_data):
        """Analyze email priority using NLP."""
        try:
            subject = email_data.get('subject', '')
            content = email_data.get('content', '')
            combined_text = f"{subject} {content}".lower()

            # Keyword detection
            doc = nlp(combined_text)
            urgent_word_count = sum(1 for token in doc
                                  if token.text in self.urgent_keywords)

            # Priority scoring
            priority_score = (
                (urgent_word_count * 2) +
                (3 if email_data.get('is_important', False) else 0) +
                (2 if self.analyze_sender_history(email_data.get('sender', '')) else 0)
            )

            # Simplified priority classification
            if priority_score >= 6:
                return "Urgent"
            elif priority_score >= 3:
                return "Follow-up"
            else:
                return "Low Priority"
        except Exception as e:
            logging.error(f"Error analyzing priority: {str(e)}")
            return "Low Priority"

    def summarize_thread(self, thread_id):
        """Generate a summary of an email thread."""
        try:
            thread = self.service.users().threads().get(
                userId='me', id=thread_id).execute()

            thread_summary = {
                'subject': '',
                'participants': set(),
                'summary': '',
                'key_points': [],
                'latest_update': '',
                'message_count': len(thread['messages'])
            }

            messages = []
            for message in thread['messages']:
                subject, sender, content = self.extract_email_content(message)
                if subject:
                    thread_summary['subject'] = subject
                if sender:
                    thread_summary['participants'].add(sender)
                if content:
                    messages.append(content)

            full_content = " ".join(messages)
            if len(full_content) > 100 and summarizer is not None:
                # Generate overall summary
                thread_summary['summary'] = summarizer(
                    full_content[:1024],
                    max_length=120,
                    min_length=30,
                    do_sample=False
                )[0]['summary_text']

                # Extract key points using spaCy
                if nlp is not None:
                    doc = nlp(full_content[:2000])
                    sentences = [sent.text.strip() for sent in doc.sents]

                    # Select key points (important sentences)
                    for sent in sentences:
                        if any keyword in sent.lower() for keyword in self.urgent_keywords:
                            thread_summary['key_points'].append(sent)

                    # Limit key points
                    thread_summary['key_points'] = thread_summary['key_points'][:3]

                # Add latest update
                if messages:
                    thread_summary['latest_update'] = messages[-1][:200] + "..."
            else:
                thread_summary['summary'] = full_content

            return thread_summary
        except Exception as e:
            logging.error(f"Error summarizing thread: {str(e)}")
            return {
                'subject': 'Error processing thread',
                'participants': set(),
                'summary': 'Could not generate summary',
                'key_points': [],
                'latest_update': '',
                'message_count': 0
            }

    def process_new_email(self, message_id):
        """Process a new email and return its priority and summary."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id).execute()

            subject, sender, content = self.extract_email_content(message)
            is_important = self.check_importance(message)

            email_data = {
                'subject': subject,
                'content': content,
                'sender': sender,
                'is_important': is_important,
                'thread_id': message.get('threadId'),
                'message_id': message_id
            }

            priority = self.analyze_priority(email_data)
            thread_summary = self.summarize_thread(email_data['thread_id'])

            # Automatically create reminder for unread emails
            if 'UNREAD' in message.get('labelIds', []):
                # Set default reminder time (5 hours from now)
                reminder_time = datetime.now(timezone.utc) + timedelta(hours=5)
                self.flag_email_for_reminder(email_data, reminder_time.isoformat())

            return {
                'priority': priority,
                'thread_summary': thread_summary,
                'email_data': email_data
            }
        except Exception as e:
            logging.error(f"Error processing email: {str(e)}")
            return {
                'priority': 'Low Priority',
                'thread_summary': {
                    'subject': 'Error processing email',
                    'summary': 'Could not process email',
                    'key_points': [],
                    'latest_update': '',
                    'message_count': 0
                },
                'email_data': {}
            }

    def get_unread_emails(self, max_results=10):
        """Get a list of unread emails."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            unread_emails = []
            
            for message_data in messages:
                message_id = message_data['id']
                email_info = self.process_new_email(message_id)
                unread_emails.append(email_info)
                
            return unread_emails
        except Exception as e:
            logging.error(f"Error getting unread emails: {str(e)}")
            return []

    def generate_email_url(self, message_id):
        """Generate a URL to view the email in Gmail."""
        return f"https://mail.google.com/mail/u/0/#inbox/{message_id}"

    def open_email_in_browser(self, message_id):
        """Open the email in a web browser."""
        try:
            email_url = self.generate_email_url(message_id)
            webbrowser.open(email_url)
            logging.info(f"Opened email {message_id} in browser")
            return True
        except Exception as e:
            logging.error(f"Error opening email in browser: {str(e)}")
            return False

    def suggest_responses(self, email_data):
        """Generate response suggestions for an email."""
        email_content = email_data.get('content', '')
        email_context = {
            'subject': email_data.get('subject', ''),
            'sender': email_data.get('sender', ''),
            'is_important': email_data.get('is_important', False)
        }

        return self.response_suggester.get_suggestions(
            email_content=email_content,
            email_context=email_context
        )

    def log_user_behavior(self, email_data, action_type):
        """Log user behavior for learning and adaptation."""
        try:
            sender = email_data.get('sender', '')
            if not sender:
                return

            behavior_data = {}
            if os.path.exists(self.behavior_file):
                with open(self.behavior_file, 'r') as f:
                    behavior_data = json.load(f)

            if sender not in behavior_data:
                behavior_data[sender] = {
                    'total_emails': 0,
                    'responses': 0,
                    'response_rate': 0.0,
                    'last_interaction': None
                }

            sender_data = behavior_data[sender]
            sender_data['total_emails'] += 1

            if action_type == 'response_sent':
                sender_data['responses'] += 1

            sender_data['response_rate'] = (
                sender_data['responses'] / sender_data['total_emails']
            )
            sender_data['last_interaction'] = datetime.now().isoformat()

            with open(self.behavior_file, 'w') as f:
                json.dump(behavior_data, f, indent=2)

        except Exception as e:
            logging.error(f"Error logging user behavior: {str(e)}")

    def create_message(self, to: str, subject: str, message_text: str, thread_id: str = None) -> dict:
        """Create an email message."""
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            msg = MIMEText(message_text)
            message.attach(msg)

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')

            email = {'raw': raw_message}
            if thread_id:
                email['threadId'] = thread_id

            return email
        except Exception as e:
            logging.error(f"Error creating message: {str(e)}")
            raise

    def send_email(self, to: str, subject: str, message_text: str, thread_id: str = None) -> dict:
        """Send an email message."""
        try:
            email = self.create_message(to, subject, message_text, thread_id)
            sent_message = self.service.users().messages().send(
                userId='me',
                body=email
            ).execute()

            logging.info(f"Message sent. Message Id: {sent_message['id']}")
            return sent_message
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            raise

    def send_quick_response(self, email_data: dict, response_text: str) -> dict:
        """Send a quick response to an email."""
        try:
            # Extract original email details
            original_sender = email_data.get('sender', '').split('<')[-1].strip('>')
            original_subject = email_data.get('subject', '')
            thread_id = email_data.get('thread_id')

            # Prepare response subject
            response_subject = (
                f"Re: {original_subject}" if not original_subject.startswith('Re:')
                else original_subject
            )

            # Send the response
            sent_message = self.send_email(
                to=original_sender,
                subject=response_subject,
                message_text=response_text,
                thread_id=thread_id
            )

            # Log the response
            self.log_user_behavior(email_data, 'response_sent')

            # Mark email as read after responding
            self.mark_email_as_read(email_data)

            return sent_message
        except Exception as e:
            logging.error(f"Error sending quick response: {str(e)}")
            raise

    def display_response_options(self, email_data):
        """Display quick response options for an email and allow selection."""
        try:
            suggestions = self.suggest_responses(email_data)
            
            print(f"\nQuick Response Options for: {email_data.get('subject', 'No Subject')}")
            print(f"From: {email_data.get('sender', 'Unknown Sender')}")
            print("-" * 50)
            
            for i, suggestion in enumerate(suggestions):
                print(f"{i+1}. {suggestion['type'].replace('_', ' ').title()}")
                print(f"   {suggestion['text'][:100]}...")
                print()
            
            print(f"{len(suggestions)+1}. Custom Response")
            print("0. Cancel")
            
            while True:
                try:
                    choice = int(input("\nSelect response option (0-{}): ".format(len(suggestions)+1)))
                    if 0 <= choice <= len(suggestions)+1:
                        break
                    print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a number.")
            
            if choice == 0:
                print("Response canceled.")
                return None
            
            if choice == len(suggestions)+1:
                # Custom response
                print("\nEnter your custom response (press Enter twice to finish):")
                lines = []
                while True:
                    line = input()
                    if not line and lines and not lines[-1]:
                        break
                    lines.append(line)
                
                custom_text = "\n".join(lines[:-1])  # Remove the last empty line
                if custom_text.strip():
                    sent_message = self.send_quick_response(email_data, custom_text)
                    print("Custom response sent successfully!")
                    return sent_message
                else:
                    print("Empty response. Canceled.")
                return sent_message
            else:
                # Send selected response
                selected = suggestions[choice-1]
                sent_message = self.send_quick_response(email_data, selected['text'])
                print(f"Response sent: {selected['type'].replace('_', ' ').title()}")
                return sent_message
        
        except Exception as e:
            logging.error(f"Error displaying response options: {str(e)}")
            print("An error occurred while processing response options.")
            return None

    def flag_email_for_reminder(self, email_data, reminder_time, reminder_type="default"):
        """Flag an email for reminder with a specified time."""
        try:
            behavior_data = self._load_behavior_data()  # Load behavior data
            sender_email = email_data.get("sender")
            message_id = email_data.get("message_id")

            if sender_email not in behavior_data:
                behavior_data[sender_email] = {
                    "total_emails": 0,
                    "responses": 0,
                    "response_rate": 0.0,
                    "last_interaction": None,
                    "reminders": {}
                }

            if "reminders" not in behavior_data[sender_email]:
                behavior_data[sender_email]["reminders"] = {}

            # Add reminder information for the message_id
            behavior_data[sender_email]["reminders"][message_id] = {
                "flagged": True,
                "status": "unanswered",
                "reminder_time": reminder_time,  # Store the ISO formatted time
                "reminder_type": reminder_type,  # "default" or "custom"
                "subject": email_data.get("subject", "No Subject")
            }

            self._save_behavior_data(behavior_data)  # Save behavior data
            logging.info(f"Email {message_id} flagged for reminder at {reminder_time}.")
            
            return True
        except Exception as e:
            logging.error(f"Error flagging email for reminder: {str(e)}")
            return False

    def mark_email_as_read(self, email_data):
        """Mark an email as read."""
        try:
            # 1. Update in Gmail (modify labels)
            message_id = email_data.get("message_id")
            if message_id:
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
            
            # 2. Update in our local tracking system
            behavior_data = self._load_behavior_data()
            sender_email = email_data.get("sender")
            
            if sender_email in behavior_data and "reminders" in behavior_data[sender_email] and \
               message_id in behavior_data[sender_email]["reminders"]:
                behavior_data[sender_email]["reminders"][message_id]["status"] = "read"
                self._save_behavior_data(behavior_data)
            
            logging.info(f"Email {message_id} marked as read.")
            return True
        except Exception as e:
            logging.error(f"Error marking email as read: {str(e)}")
            return False

    def check_reminders(self):
        """Check for reminders that are due and take action."""
        try:
            behavior_data = self._load_behavior_data()
            now = datetime.now(timezone.utc)
            due_reminders = []

            # First pass: collect all due reminders
            for sender_email, sender_data in behavior_data.items():
                if "reminders" not in sender_data:
                    continue  # Skip senders without reminders

                for message_id, reminder_data in sender_data["reminders"].items():
                    if not reminder_data.get("flagged", False):  # Skip if not flagged
                        continue
                    
                    if reminder_data.get("status", "") != "unanswered":  # Skip if already read
                        continue
                    
                    try:
                        reminder_time = datetime.fromisoformat(reminder_data["reminder_time"])
                        if reminder_time.tzinfo is None:
                            reminder_time = reminder_time.replace(tzinfo=timezone.utc)
                    except ValueError as ve:
                        logging.error(f"Error parsing reminder time for email {message_id}: {ve}")
                        continue

                    if now >= reminder_time:
                        due_reminders.append({
                            "sender_email": sender_email,
                            "message_id": message_id,
                            "subject": reminder_data.get("subject", "No Subject"),
                            "reminder_time": reminder_time
                        })

            # Second pass: handle all due reminders
            if due_reminders:
                print("\n" + "=" * 60)
                print(f"You have {len(due_reminders)} email reminder(s) due:")
                print("=" * 60)
                
                for i, reminder in enumerate(due_reminders):
                    print(f"\n{i+1}. From: {reminder['sender_email']}")
                    print(f"   Subject: {reminder['subject']}")
                    print(f"   Reminder set for: {reminder['reminder_time'].strftime('%Y-%m-%d %H:%M')}")
                    
                    self._handle_single_reminder(reminder)
            else:
                logging.info("No reminders due at this time.")

            return len(due_reminders)
        except Exception as e:
            logging.error(f"Error checking reminders: {str(e)}")
            return 0

    def _handle_single_reminder(self, reminder):
        """Handle a single reminder with options."""
        print("\nOptions:")
        print("1. Read Now (Open Email)")
        print("2. Mark as Read")
        print("3. Remind Later (Default: +5 Hours)")
        print("4. Remind Later (Custom Hours)")
        print("5. Remind Later (Custom Date & Time)")

        while True:
            try:
                choice = int(input("\nSelect option (1-5): "))
                if 1 <= choice <= 5:
                    break
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number between 1 and 5.")

        sender_email = reminder["sender_email"]
        message_id = reminder["message_id"]
        email_data = {"sender": sender_email, "message_id": message_id, "subject": reminder["subject"]}

        if choice == 1:
            # Read Now (Open in browser)
            if self.open_email_in_browser(message_id):
                print(f"Opening email in browser...")
                self.mark_email_as_read(email_data)
                
                # Ask if user wants to respond
                respond = input("\nWould you like to send a quick response? (y/n): ").lower()
                if respond == 'y':
                    self.display_response_options(email_data)
            else:
                print("Failed to open email in browser.")
                
        elif choice == 2:
            # Mark as Read without opening
            if self.mark_email_as_read(email_data):
                print(f"Email marked as read.")
            else:
                print("Failed to mark email as read.")
                
        elif choice == 3:
            # Default Remind Later (5 hours)
            new_reminder_time = datetime.now(timezone.utc) + timedelta(hours=5)
            if self.flag_email_for_reminder(email_data, new_reminder_time.isoformat(), reminder_type="default"):
                print(f"Reminder rescheduled for {new_reminder_time.strftime('%Y-%m-%d %H:%M')}.")
            else:
                print("Failed to reschedule reminder.")
                
        elif choice == 4:
            # Custom Remind Later (Hours)
            try:
                hours = float(input("Remind again after how many hours? "))
                if hours <= 0:
                    print("Hours must be positive. Using default 5 hours.")
                    hours = 5
                    
                new_reminder_time = datetime.now(timezone.utc) + timedelta(hours=hours)
                if self.flag_email_for_reminder(email_data, new_reminder_time.isoformat(), reminder_type="custom"):
                    print(f"Reminder rescheduled for {new_reminder_time.strftime('%Y-%m-%d %H:%M')}.")
                else:
                    print("Failed to reschedule reminder.")
            except ValueError:
                print("Invalid input. Using default 5 hours.")
                new_reminder_time = datetime.now(timezone.utc) + timedelta(hours=5)
                self.flag_email_for_reminder(email_data, new_reminder_time.isoformat(), reminder_type="default")
                
        elif choice == 5:
            # Custom Remind Later (Date & Time)
            while True:
                try:
                    date_str = input("Enter date (YYYY-MM-DD): ")
                    time_str = input("Enter time (HH:MM): ")
                    custom_datetime_str = f"{date_str} {time_str}"
                    custom_reminder_time = datetime.strptime(custom_datetime_str, "%Y-%m-%d %H:%M")
                    
                    # Add timezone information
                    custom_reminder_time = custom_reminder_time.replace(tzinfo=timezone.utc)
                    
                    # Check if time is in the future
                    if custom_reminder_time <= datetime.now(timezone.utc):
                        print("Reminder time must be in the future. Please try again.")
                        continue
                        
                    if self.flag_email_for_reminder(email_data, custom_reminder_time.isoformat(), reminder_type="custom"):
                        print(f"Reminder rescheduled for {custom_reminder_time.strftime('%Y-%m-%d %H:%M')}.")
                        break
                    else:
                        print("Failed to reschedule reminder.")
                        break
                except ValueError:
                    print("Invalid date/time format. Please use YYYY-MM-DD for date and HH:MM for time.")

        # Update status in behavior data
        behavior_data = self._load_behavior_data()
        if sender_email in behavior_data and "reminders" in behavior_data[sender_email] and \
            message_id in behavior_data[sender_email]["reminders"]:
            
            # If rescheduled (options 3,4,5), we've already updated. Otherwise, unflag.
            if choice < 3:
                behavior_data[sender_email]["reminders"][message_id]["flagged"] = False
                self._save_behavior_data(behavior_data)

    def _load_behavior_data(self):
        """Load user behavior data from file."""
        try:
            if not os.path.exists(self.behavior_file):
                return {}
            with open(self.behavior_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Behavior file {self.behavior_file} not found.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error in behavior file: {str(e)}")
            return {}

    def _save_behavior_data(self, data):
        """Save user behavior data to file."""
        try:
            with open(self.behavior_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving behavior data: {str(e)}")
            return False
