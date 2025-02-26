from transformers import pipeline
import os

# Get the Hugging Face token from the environment variable
huggingface_token = os.getenv("HUGGINGFACE_TOKEN")

# Initialize a pre-trained model for text generation
model_name = "gpt2"  # Use the correct model identifier
reply_generator = pipeline('text-generation', model=model_name, use_auth_token=huggingface_token)

def generate_smart_reply(message):
    # Use the pre-trained model to generate a reply
    response = reply_generator(message, max_new_tokens=50, truncation=True)
    smart_reply = response[0]['generated_text']
    
    # Return the smart reply
    return smart_reply
