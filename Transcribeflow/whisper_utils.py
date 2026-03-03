import whisper

# Load model once
model = whisper.load_model("base")

def transcribe_audio(audio_file):
    result = model.transcribe(audio_file)
    return result["text"]