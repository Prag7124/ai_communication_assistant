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
        if any(keyword in email_content.lower() for keyword in ["meet", "meeting", "appointment", "schedule", "calendar"]):
            suggestions.append({
                "type": "meeting_accept",
                "text": self.common_responses["meeting_accept"]
            })
            suggestions.append({
                "type": "meeting_reject",
                "text": self.common_responses["meeting_reject"]
            })
        
        # Check for questions or info requests
        if "?" in email_content or any(keyword in email_content.lower() for keyword in ["question", "inquiry", "help", "information", "details"]):
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
