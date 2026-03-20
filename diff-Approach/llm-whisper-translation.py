import os
import time
import json
import argparse
from dotenv import load_dotenv
from pyannoteai.sdk import Client
from openai import OpenAI

# ==========================================
# 1. SETUP & CREDENTIALS
# ==========================================
load_dotenv()
PYANNOTE_KEY = os.getenv("PYANNOTE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not PYANNOTE_KEY or not OPENAI_KEY:
    raise ValueError("Missing API Keys. Please check your .env file.")

pyannote_client = Client(PYANNOTE_KEY)
openai_client = OpenAI(api_key=OPENAI_KEY)

# ==========================================
# 2. API ABSTRACTIONS
# ==========================================
def get_pyannote_diarization(audio_path):
    print("[1/4] Calling Pyannote API for Speaker Diarization...")
    media_url = pyannote_client.upload(audio_path)
    job_id = pyannote_client.diarize(media_url, model="precision-2", transcription=True)
    
    while True:
        job = pyannote_client.retrieve(job_id)
        if job["status"] == "succeeded":
            return job["output"]["turnLevelTranscription"]
        elif job["status"] in ["failed", "canceled"]:
            raise Exception("Pyannote API Job failed.")
        time.sleep(5)

def get_openai_translation(audio_path):
    print("[2/4] Calling OpenAI Whisper API for pure English Translation...")
    with open(audio_path, "rb") as audio_file:
        response = openai_client.audio.translations.create(
            model="whisper-1", 
            file=audio_file,
            response_format="verbose_json"
        )
    # The new OpenAI Python SDK returns an object with a .segments property
    return response.segments

# ==========================================
# 3. THE CLOUD STITCH (Merging APIs)
# ==========================================
def merge_speakers_and_translation(openai_segments, pyannote_blocks):
    print("[3/4] Stitching Pyannote Speakers with OpenAI English text...")
    
    merged_script = ""
    
    for seg in openai_segments:
        # Handle both dictionary and object formats from the OpenAI SDK safely
        seg_start = seg.start if hasattr(seg, 'start') else seg['start']
        seg_end = seg.end if hasattr(seg, 'end') else seg['end']
        seg_text = seg.text.strip() if hasattr(seg, 'text') else seg['text'].strip()
        
        if not seg_text:
            continue

        best_speaker = "UNKNOWN"
        max_overlap = 0

        # Find which Pyannote speaker was talking during this timeframe
        for block in pyannote_blocks:
            overlap_start = max(seg_start, block["start"])
            overlap_end = min(seg_end, block["end"])
            overlap_duration = overlap_end - overlap_start

            if overlap_duration > max_overlap:
                max_overlap = overlap_duration
                best_speaker = block["speaker"]

        # Format timestamps as MM:SS for the LLM
        start_fmt = f"{int(seg_start // 60):02d}:{int(seg_start % 60):02d}"
        end_fmt = f"{int(seg_end // 60):02d}:{int(seg_end % 60):02d}"
        
        merged_script += f"[{start_fmt} - {end_fmt}] {best_speaker}: {seg_text}\n"

    return merged_script

# ==========================================
# 4. LLM ROUTER
# ==========================================
def extract_boundaries_with_llm(script_text):
    print("[4/4] Routing stitched English script to GPT-4o-mini...")
    
    system_prompt = """
    You are an AI analyzing a translated English transcript from a retail store.
    The salesman is wearing the microphone. 
    
    RULES:
    1. Ignore background friends chatting with the salesman.
    2. Identify the exact Start and End times of the TWO distinct customer interactions.
    3. Customers don't always say "Hello". Look for product queries (e.g., "Do you have this?").
    4. Bridge long billing pauses if the semantic transaction continues after the pause.
    
    Output ONLY a valid JSON object in this format. No markdown, no extra text:
    {
      "Conversation_1": {"start": "MM:SS", "end": "MM:SS"},
      "Conversation_2": {"start": "MM:SS", "end": "MM:SS"}
    }
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n\n{script_text}"}
        ],
        temperature=0.1
    )
    
    raw_output = response.choices[0].message.content.strip()
    
    # Strip markdown if the LLM adds it
    if raw_output.startswith("```json"): 
        raw_output = raw_output[7:]
    if raw_output.endswith("```"): 
        raw_output = raw_output[:-3]
        
    return json.loads(raw_output.strip())

# ==========================================
# 5. COMMAND LINE EXECUTION
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Cloud API Fusion Pipeline.")
    parser.add_argument("audio_file", type=str, help="Path to the audio file")
    
    args = parser.parse_args()
    target_audio = args.audio_file
    
    if not os.path.exists(target_audio):
        print(f"Error: Could not find the file '{target_audio}'")
        exit(1)
        
    try:
        # Run the API calls
        pyannote_data = get_pyannote_diarization(target_audio)
        openai_data = get_openai_translation(target_audio)
        
        # Merge the data mathematically
        final_script = merge_speakers_and_translation(openai_data, pyannote_data)
        
        # Send the clean script to the LLM to get the boundaries
        boundaries = extract_boundaries_with_llm(final_script)
        
        print("\n" + "="*50)
        print(f"FINAL BOUNDARIES FOR: {os.path.basename(target_audio)}")
        print("="*50)
        print(json.dumps(boundaries, indent=2))
        
    except Exception as e:
        print(f"\nPipeline Error: {e}")