import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ==========================================
# 1. SETUP & CREDENTIALS
# ==========================================
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_AI_API")

if not GEMINI_KEY:
    raise ValueError("Missing GEMINI_AI_API in .env")

client = genai.Client(api_key=GEMINI_KEY)
MODEL_ID = "gemini-2.5-flash"

# ==========================================
# 2. STRICT JSON SCHEMA (Pydantic)
# ==========================================
class ConversationBoundary(BaseModel):
    start_seconds: float = Field(description="Start time of the interaction in seconds")
    end_seconds: float = Field(description="End time of the interaction in seconds")
    confidence: str = Field(description="high, medium, or low")
    notes: str = Field(description="Any observed context, like abrupt queries")

class AudioAnalysis(BaseModel):
    analysis: str = Field(description="2-sentence summary of what you heard")
    Conversation_1: ConversationBoundary
    Conversation_2: ConversationBoundary

# ==========================================
# 3. LOCAL VAD & TIMESTAMP LEDGER
# ==========================================
def compress_audio_and_build_ledger(input_path: str, output_path: str):
    print(f"\n[1/4] Running Local VAD to strip silence from {input_path}...")
    
    # Load the audio (pydub relies on ffmpeg under the hood)
    audio = AudioSegment.from_file(input_path)
    
    # Detect non-silent chunks. 
    # min_silence_len=2000 means any silence longer than 2 seconds gets cut.
    # silence_thresh=-40 is a standard decibel threshold for retail background hum.
    print("      Detecting speech segments...")
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=2000, silence_thresh=-40)
    
    if not nonsilent_ranges:
        raise ValueError("No speech detected in the audio file!")

    compressed_audio = AudioSegment.empty()
    mapping_ledger = []
    current_new_time_ms = 0.0

    print("      Building Compressed Audio and Timestamp Ledger...")
    for orig_start_ms, orig_end_ms in nonsilent_ranges:
        # 1. Slice the actual audio
        chunk = audio[orig_start_ms:orig_end_ms]
        compressed_audio += chunk
        
        # 2. Record the ledger entry (converting ms to seconds)
        duration_ms = orig_end_ms - orig_start_ms
        new_start_ms = current_new_time_ms
        new_end_ms = current_new_time_ms + duration_ms
        
        mapping_ledger.append({
            "orig_start": orig_start_ms / 1000.0,
            "orig_end": orig_end_ms / 1000.0,
            "new_start": new_start_ms / 1000.0,
            "new_end": new_end_ms / 1000.0
        })
        
        current_new_time_ms += duration_ms

    # Export the much smaller audio file
    compressed_audio.export(output_path, format="mp3", bitrate="64k")
    
    orig_dur = len(audio) / 1000.0
    new_dur = len(compressed_audio) / 1000.0
    print(f"      Compression complete! Reduced from {orig_dur:.1f}s to {new_dur:.1f}s.")
    
    return mapping_ledger

def get_original_time(compressed_time_sec, mapping_ledger):
    """Translates Gemini's timestamp back to the original audio timeline."""
    for block in mapping_ledger:
        if block["new_start"] <= compressed_time_sec <= block["new_end"]:
            offset = compressed_time_sec - block["new_start"]
            return block["orig_start"] + offset
    
    # Fallback to the very end if out of bounds
    return mapping_ledger[-1]["orig_end"]

def format_time(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

# ==========================================
# 4. GEMINI CLOUD PROCESSING
# ==========================================
def upload_audio(audio_path: str):
    print(f"\n[2/4] Uploading compressed audio to Gemini Files API...")
    uploaded = client.files.upload(
        file=audio_path,
        config=types.UploadFileConfig(mime_type="audio/mpeg")
    )

    while uploaded.state.name == "PROCESSING":
        time.sleep(2)
        uploaded = client.files.get(name=uploaded.name)

    if uploaded.state.name == "FAILED":
        raise RuntimeError(f"Gemini file upload failed: {uploaded.name}")

    return uploaded

def analyze_audio_with_gemini(uploaded_file):
    print("\n[3/4] Gemini is analyzing the compressed audio natively...")

    prompt = """
You are analyzing a real-world audio recording from a lapel microphone worn by a salesman in an Indian retail store.

CRITICAL CONTEXT:
This audio has been TIME-COMPRESSED. All long silences (like 5-minute billing pauses) have been artificially removed. 
A conversation that originally took 10 minutes might happen in 2 minutes of dense audio. 
Do NOT rely on pauses to figure out when a customer leaves. You must rely purely on the SEMANTIC flow of the interaction.

FACTS ABOUT THIS RECORDING:
1. The salesman wears the lapel mic and speaks THROUGHOUT the entire recording.
2. The salesman casually chats with background colleagues/friends at various points. IGNORE these completely.
3. TWO distinct customers visit the store.
4. Customers speak in Kannada, Hindi, English, or a mix.
5. Customers do NOT use formal greetings. They start abruptly with product requests ("do you have this size?", "how much is this?").

YOUR TASK:
Listen to the audio. Identify the precise start and end timestamps (in seconds) of the TWO distinct customer interactions in this compressed audio.
"""

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            types.Part.from_uri(file_uri=uploaded_file.uri, mime_type="audio/mpeg"),
            prompt
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=AudioAnalysis, 
        )
    )
    
    return json.loads(response.text)

# ==========================================
# 5. EXECUTION & LEDGER TRANSLATION
# ==========================================
if __name__ == "__main__":
    original_audio_path = "audio/sample3KN.mp3" 
    temp_compressed_path = "audio/temp_compressed.mp3"

    if not Path(original_audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {original_audio_path}")

    uploaded_file = None
    try:
        # 1. Compress and map the audio
        ledger = compress_audio_and_build_ledger(original_audio_path, temp_compressed_path)
        
        # 2. Upload the tiny file
        uploaded_file = upload_audio(temp_compressed_path)
        
        # 3. Get the raw result from Gemini
        gemini_result = analyze_audio_with_gemini(uploaded_file)

        print("\n[4/4] Translating timestamps back to reality using Ledger...")
        
        print("\n" + "=" * 52)
        print(f"FINAL TRUE BOUNDARIES (VAD + Gemini {MODEL_ID})")
        print("=" * 52)

        print(f"\nAnalysis: {gemini_result['analysis']}\n")

        for conv_key in ["Conversation_1", "Conversation_2"]:
            c = gemini_result[conv_key]
            
            # Use the ledger to find the TRUE original times
            true_start_sec = get_original_time(c["start_seconds"], ledger)
            true_end_sec = get_original_time(c["end_seconds"], ledger)
            
            conf = c["confidence"]
            notes = c["notes"]
            label = conv_key.replace("_", " ")
            
            print(f"{label}: [ {format_time(true_start_sec)} --> {format_time(true_end_sec)} ] (Confidence: {conf})")
            if notes:
                print(f"           Note: {notes}")

    except Exception as e:
        print(f"\nPipeline Error: {e}")

    finally:
        # Cleanup Cloud File
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
        # Cleanup Local Temp File
        if os.path.exists(temp_compressed_path):
            os.remove(temp_compressed_path)