import os
import time
from dotenv import load_dotenv
from pyannoteai.sdk import Client
load_dotenv()
API_KEY = os.getenv("PYANNOTE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found. Please check your .env file.")
client = Client(API_KEY)
def get_transcript_data(audio_path):
    print(f"\n[1/3] Uploading {audio_path}...")
    media_url = client.upload(audio_path)
    print("[2/3] Processing STT + Diarization...")
    job_id = client.diarize(media_url, model="precision-2", transcription=True)
    while True:
        job = client.retrieve(job_id)
        if job["status"] == "succeeded":
            return job["output"]["turnLevelTranscription"]
        elif job["status"] in ["failed", "canceled"]:
            raise Exception("API Job failed.")
        time.sleep(5)
def find_start_anchor(transcript, customer_start, staff_id):
    """Finds the staff's greeting right before the customer interaction starts."""
    greetings = ["hello", "hi", "welcome", "namaste", "namaskara", "morning", "sir", "ma'am", "nodona", "waiting"]
    best_start = customer_start
    for block in transcript:
        if (customer_start - 45.0) <= block["start"] <= customer_start:
            if block["speaker"] == staff_id:
                if any(word in block["text"].lower() for word in greetings):
                    best_start = block["start"]
                    break 
    return best_start
def find_end_anchor(transcript, customer_end, staff_id):
    """Finds the staff's farewell right after the customer finishes."""
    farewells = ["thank", "dhanyavada", "bill", "swipe", "cash", "bye", "day", "done"]
    best_end = customer_end
    for block in transcript:
        if customer_end <= block["end"] <= (customer_end + 30.0):
            if block["speaker"] == staff_id:
                if any(word in block["text"].lower() for word in farewells):
                    best_end = max(best_end, block["end"])
    return best_end
def analyze_lapel_sessions(transcript):
    print("[3/3] Executing Lapel Mic Protocol (Ephemerality Filtering)...")
    if not transcript:
        return None
    file_duration = transcript[-1]["end"]
    speaker_stats = {}
    for block in transcript:
        spk = block["speaker"]
        if spk not in speaker_stats:
            speaker_stats[spk] = {"turns": 0, "first": block["start"], "last": block["end"]}
        speaker_stats[spk]["turns"] += 1
        speaker_stats[spk]["last"] = block["end"]
    main_staff = max(speaker_stats, key=lambda x: speaker_stats[x]["turns"])
    valid_customers = []
    print(f"      -> Salesman Identified: {main_staff}")
    for spk, stats in speaker_stats.items():
        if spk == main_staff: continue
        spread = stats["last"] - stats["first"]
        if spread > (file_duration * 0.65):
            print(f"      -> Dropped {spk} (Identified as Colleague/Friend)")
        elif stats["turns"] < 3:
            pass
        else:
            valid_customers.append(spk)
    customer_blocks = [b for b in transcript if b["speaker"] in valid_customers]
    if not customer_blocks:
        print("Warning: No valid customers found.")
        return None
    merged_sessions = []
    MERGE_THRESHOLD = 240.0
    for block in customer_blocks:
        if not merged_sessions:
            merged_sessions.append({"start": block["start"], "end": block["end"]})
            continue
        last_session = merged_sessions[-1]
        if (block["start"] - last_session["end"]) <= MERGE_THRESHOLD:
            last_session["end"] = max(last_session["end"], block["end"])
        else:
            merged_sessions.append({"start": block["start"], "end": block["end"]})
    merged_sessions.sort(key=lambda x: x["end"] - x["start"], reverse=True)
    if len(merged_sessions) < 2:
        print("Warning: Could not isolate two distinct conversations.")
        return None
    final_2_conversations = merged_sessions[:2]
    final_2_conversations.sort(key=lambda x: x["start"])
    results = {}
    for i, conv in enumerate(final_2_conversations):
        start_actual = find_start_anchor(transcript, conv["start"], main_staff)
        end_actual = find_end_anchor(transcript, conv["end"], main_staff)
        results[f"Conversation {i+1}"] = {"start": start_actual, "end": end_actual}
    return results
if __name__ == "__main__":
    audio_file = "audio/Sample2EN.mp3"
    try:
        raw_transcript = get_transcript_data(audio_file)
        boundaries = analyze_lapel_sessions(raw_transcript)
        if boundaries:
            print("\n" + "="*40)
            print("FINAL CONVERSATION BOUNDARIES")
            print("="*40)
            def format_time(seconds):
                return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
            for conv, times in boundaries.items():
                print(f"{conv}: [ {format_time(times['start'])} --> {format_time(times['end'])} ]")
    except Exception as e:
        print(f"\nPipeline Error: {e}")