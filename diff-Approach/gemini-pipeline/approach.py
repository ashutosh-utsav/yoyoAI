import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_AI_API")
if not GEMINI_KEY:
    raise ValueError("Missing GEMINI_AI_API in .env")
client = genai.Client(api_key=GEMINI_KEY)
MODEL_ID = "gemini-2.5-flash"
def upload_audio(audio_path: str):
    """
    Uploads the audio file to Gemini Files API.
    Handles polling until the file is ACTIVE and ready.
    """
    print(f"\n[1/2] Uploading '{audio_path}' to Gemini Files API...")
    print(f"      Using model: {MODEL_ID}")
    uploaded = client.files.upload(
        file=audio_path,
        config=types.UploadFileConfig(mime_type="audio/mpeg")
    )
    print("      Waiting for file to be processed...")
    while uploaded.state.name == "PROCESSING":
        time.sleep(3)
        uploaded = client.files.get(name=uploaded.name)
    if uploaded.state.name == "FAILED":
        raise RuntimeError(f"Gemini file upload failed: {uploaded.name}")
    print(f"      File ready: {uploaded.uri}")
    return uploaded
def analyze_audio_with_gemini(uploaded_file) -> dict:
    """
    Sends the audio directly to Gemini 2.5 Flash.
    No STT, no diarization, no alignment needed.
    Gemini LISTENS to the audio and reasons directly.
    Language agnostic: Kannada, Hindi, English, codemix.
    """
    print("\n[2/2] Sending audio to Gemini for conversation boundary analysis...")
    print("      Gemini is listening to the full audio file now...")
    prompt = """
You are analyzing a real-world audio recording from a lapel microphone worn by a salesman in an Indian retail store.
FACTS ABOUT THIS RECORDING:
1. The salesman wears the lapel mic and speaks THROUGHOUT the entire recording.
2. The salesman casually chats with background colleagues/friends at various points.  IGNORE these completely.
3. TWO distinct customers visit the store:
   - Customer 1 visits first, asks about products, may wait silently during billing (2-5 minutes), then leaves.
   - Customer 2 visits later, same pattern.
4. Customers speak in Kannada, Hindi, English, or a mix — this is completely normal.
5. CRITICAL RULE — Billing Pause: A silence of 2 to 5 minutes CAN happen MID-TRANSACTION while the salesman processes payment or checks inventory. This silence does NOT mean the customer has left. The same customer continues after the silence. Look at context BEFORE and AFTER any silence.
6. Customers do NOT use formal greetings. They start abruptly with product requests like "do you have this size?", "how much is this?", "show me that one."
YOUR TASK:
Listen to the full audio carefully. Identify the precise start and end timestamps of the TWO distinct customer interactions.
Return ONLY a valid raw JSON object, no markdown. Use this exact format:
{
  "analysis": "2-sentence summary of what you heard and how you determined the boundaries",
  "Conversation_1": {
    "start_seconds": 0.0,
    "end_seconds": 0.0,
    "start_fmt": "MM:SS",
    "end_fmt": "MM:SS",
    "confidence": "high or medium or low",
    "notes": "any observed uncertainty, billing pause detected, etc."
  },
  "Conversation_2": {
    "start_seconds": 0.0,
    "end_seconds": 0.0,
    "start_fmt": "MM:SS",
    "end_fmt": "MM:SS",
    "confidence": "high or medium or low",
    "notes": "any observed uncertainty"
  }
}
"""
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            types.Part.from_uri(
                file_uri=uploaded_file.uri,
                mime_type="audio/mpeg"
            ),
            prompt
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )
    raw = response.text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())
def delete_uploaded_file(uploaded_file):
    """Remove the file from Gemini Files API after use."""
    try:
        client.files.delete(name=uploaded_file.name)
        print(f"      Cleaned up uploaded file: {uploaded_file.name}")
    except Exception:
        pass
if __name__ == "__main__":
    audio_file_path = "audio/sample3KN.mp3"
    if not Path(audio_file_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    uploaded = None
    try:
        uploaded = upload_audio(audio_file_path)
        result   = analyze_audio_with_gemini(uploaded)
        print("\n" + "=" * 52)
        print(f"FINAL RESULTS  (Gemini {MODEL_ID})")
        print("=" * 52)
        if "analysis" in result:
            print(f"\n  Analysis: {result['analysis']}\n")
        for conv_key in ["Conversation_1", "Conversation_2"]:
            if conv_key in result:
                c     = result[conv_key]
                start = c.get("start_fmt", "??:??")
                end   = c.get("end_fmt",   "??:??")
                conf  = c.get("confidence", "?")
                notes = c.get("notes", "")
                label = conv_key.replace("_", " ")
                print(f"  {label}: [ {start} --> {end} ]  (confidence: {conf})")
                if notes:
                    print(f"           Note: {notes}")
        print("\n  --- Full JSON ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\nPipeline Error: {e}")
        raise
    finally:
        if uploaded:
            delete_uploaded_file(uploaded)