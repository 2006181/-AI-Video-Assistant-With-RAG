from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from dotenv import load_dotenv
load_dotenv()
import os

print("key Loaded:", os.getenv("SARAVAM_API_KEY"))
print("CWD:", os.getcwd())

source = "https://youtu.be/UUnAH-_0Dv4?si=hiUnMLRwudErSxH0"
language = "hinglish" #change to "hinglish" to test Sarvam

chunks = process_input(source)
transcript = transcribe_all(chunks, language=language)

print("\n=== Transcript ===\n")
print(transcript)
