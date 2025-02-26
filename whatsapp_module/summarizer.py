from transformers import pipeline

# Initialize a pre-trained model for text summarization
summarizer = pipeline("summarization")

def summarize_text(conversation):
    # Use the pre-trained model to generate a summary
    summary = summarizer(conversation, max_length=100, min_length=30, do_sample=False)
    summarized_text = summary[0]['summary_text']
    
    # Return the summarized text
    return summarized_text
