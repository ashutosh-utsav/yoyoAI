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

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_AI_API")

if not GEMINI_KEY:
    raise ValueError("Missing GEMINI_AI_API in .env")

client = genai.Client(api_key=GEMINI_KEY)
MODEL_ID = "gemini-2.5-flash"

class ConversationBoundary(BaseModel):
    start_time: str = Field(description="Start time of the interaction in MM:SS format")
    end_time: str = Field(description="End time of the interaction in MM:SS format")
    confidence: str = Field(description="high, medium, or low")
    notes: str = Field(description="Any observed context, like abrupt queries")

class AudioAnalysis(BaseModel):
    analysis: str = Field(description="2-sentence summary of what you heard")
    Conversation_1: ConversationBoundary
    Conversation_2: ConversationBoundary

def compress_audio_and_build_ledger(input_path: str, output_path: str):
    print(f"\n[1/4] Running Local VAD to strip silence from {input_path}...")
    
    audio = AudioSegment.from_file(input_path)
    
    print("      Detecting speech segments...")

    #TODO: Implement dynamic noise-floor detection for the VAD threshold to handle different retail environments (e.g., quiet boutiques vs. loud markets)
    #TODO: Add support for different audio formats (WAV, FLAC, etc.)
    
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=2000, silence_thresh=-40)
    
    if not nonsilent_ranges:
        raise ValueError("No speech detected in the audio file!")

    compressed_audio = AudioSegment.empty()
    mapping_ledger = []
    current_new_time_ms = 0.0

    print("      Building Compressed Audio and Timestamp Ledger...")
    for orig_start_ms, orig_end_ms in nonsilent_ranges:
        chunk = audio[orig_start_ms:orig_end_ms]
        compressed_audio += chunk
        
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

    compressed_audio.export(output_path, format="mp3", bitrate="64k")
    
    orig_dur = len(audio) / 1000.0
    new_dur = len(compressed_audio) / 1000.0
    print(f"      Compression complete! Reduced from {orig_dur:.1f}s to {new_dur:.1f}s.")
    
    return mapping_ledger

def get_original_time(compressed_time_sec, mapping_ledger):
    for block in mapping_ledger:
        if block["new_start"] <= compressed_time_sec <= block["new_end"]:
            offset = compressed_time_sec - block["new_start"]
            return block["orig_start"] + offset
    
    return mapping_ledger[-1]["orig_end"]

def format_time(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

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
Listen to the audio. Identify the precise start and end timestamps (IN MM:SS FORMAT) of the TWO distinct customer interactions IN THIS COMPRESSED AUDIO.
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

if __name__ == "__main__":
    import glob
    import os
    import json
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audio_dir = os.path.join(base_path, "audio")
    audio_files = glob.glob(os.path.join(audio_dir, "*.mp3"))
    
    if not audio_files:
        print(f"No audio files found in {audio_dir}.")
        
    evaluation_results = {}
        
    for original_audio_path in audio_files:
        filename = os.path.basename(original_audio_path)
        print("\n" + "="*70)
        print(f"PROCESSING EXTERNAL AUDIO FILE: {original_audio_path}")
        print("="*70)
        
        temp_compressed_path = os.path.join(audio_dir, "temp_compressed.mp3")

        uploaded_file = None
        try:
            ledger = compress_audio_and_build_ledger(original_audio_path, temp_compressed_path)
            uploaded_file = upload_audio(temp_compressed_path)
            gemini_result = analyze_audio_with_gemini(uploaded_file)

            def parse_mmss(time_str: str) -> float:
                try:
                    parts = time_str.split(":")
                    if len(parts) == 2:
                        return float(parts[0]) * 60 + float(parts[1])
                    elif len(parts) == 3:
                        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    pass
                return 0.0

            file_eval = {}
            for conv_key in ["Conversation_1", "Conversation_2"]:
                if conv_key not in gemini_result:
                    continue
                c = gemini_result[conv_key]
                compressed_start_sec = parse_mmss(c.get("start_time", "00:00"))
                compressed_end_sec = parse_mmss(c.get("end_time", "00:00"))

                true_start_sec = get_original_time(compressed_start_sec, ledger)
                true_end_sec = get_original_time(compressed_end_sec, ledger)
                
                label = conv_key.replace("_", " ")
                file_eval[label] = {
                    "start": round(true_start_sec, 2),
                    "end": round(true_end_sec, 2)
                }
            
            evaluation_results[filename] = file_eval
            print(f"-> Successfully processed {filename}")

        except Exception as e:
            print(f"\nPipeline Error on {filename}: {e}")

        finally:
            if uploaded_file:
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass
            if os.path.exists(temp_compressed_path):
                os.remove(temp_compressed_path)
                
    print("\n" + "=" * 52)
    print("EVALUATION OUTPUT (JSON FORMAT)")
    print("=" * 52)
    print(json.dumps(evaluation_results, indent=2))
