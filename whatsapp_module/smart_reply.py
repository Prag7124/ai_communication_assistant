from transformers import pipeline

# Initialize a pre-trained model for text generation
reply_generator = pipeline('text-generation', model='gpt-2')

def generate_smart_reply(message):
    # Use the pre-trained model to generate a reply
    response = reply_generator(message, max_length=50, num_return_sequences=1)
    smart_reply = response[0]['generated_text']
    
    # Return the smart reply
    return smart_reply
