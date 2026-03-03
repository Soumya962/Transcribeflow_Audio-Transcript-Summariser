from transformers import pipeline

# Load model once
summarizer = pipeline("summarization", model="t5-small")

def summarize_text(text):

    if not text:
        return ""

    # If text is too short, don't summarize
    if len(text.split()) < 30:
        return text.strip()

    summary = summarizer(
        text,
        max_length=60,
        min_length=25,
        do_sample=False
    )

    return summary[0]['summary_text']