import json
from typing import List, Dict
import logging
import os


class ResponseSuggester:
    def __init__(self, templates_path='utils/response_templates.json'):
        """Initialize the response suggester with templates from JSON file."""
        self.templates_path = templates_path
        self.response_templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """Load response templates from JSON file."""
        try:
            if not os.path.exists(self.templates_path):
                logging.error(f"Response templates file not found: {self.templates_path}")
                return {}
            
            with open(self.templates_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Response templates file not found: {self.templates_path}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error in templates file: {str(e)}")
            return {}

    def get_suggestions(self, email_content: str, email_context: Dict) -> List[Dict]:
        """Generate contextual response suggestions based on email content and context."""
        try:
            suggestions = []
            subject = email_context.get('subject', '').lower()
            is_urgent = email_context.get('is_important', False)

            # Add urgent responses if email is marked important
            if is_urgent and 'urgent' in self.response_templates:
                suggestions.extend([
                    {'text': template, 'type': 'urgent'}
                    for template in self.response_templates['urgent']
                ])

            # Add meeting-related responses if detected
            if 'meeting' in subject and 'meeting' in self.response_templates:
                suggestions.extend([
                    {'text': template, 'type': 'meeting'}
                    for template in self.response_templates['meeting']
                ])

            # Add acknowledgment responses
            if 'acknowledgment' in self.response_templates:
                suggestions.extend([
                    {'text': template, 'type': 'acknowledgment'}
                    for template in self.response_templates['acknowledgment']
                ])

            # Limit to top 5 most relevant suggestions
            return suggestions[:5]

        except Exception as e:
            logging.error(f"Error generating suggestions: {str(e)}")
            return []

