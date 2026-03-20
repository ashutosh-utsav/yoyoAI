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


def analyze_sessions(transcript):
    print("[3/3] Executing Deterministic Session Merging...")
    speaker_stats = {}
    for block in transcript:
        spk = block["speaker"]
        if spk not in speaker_stats:
            speaker_stats[spk] = {"turns": 0, "start": block["start"], "end": block["end"]}
        speaker_stats[spk]["turns"] += 1
        speaker_stats[spk]["end"] = block["end"]
    main_staff = max(speaker_stats, key=lambda x: speaker_stats[x]["turns"])
    staff_timeline = [b for b in transcript if b["speaker"] == main_staff]
    customer_sessions = []
    for spk, stats in speaker_stats.items():
        if spk != main_staff and stats["turns"] > 3:
            customer_sessions.append({
                "speakers": [spk],
                "start": stats["start"],
                "end": stats["end"]
            })
    customer_sessions.sort(key=lambda x: x["start"])
    merged_sessions = []
    merge_threshold_seconds = 180.0 
    for current in customer_sessions:
        if not merged_sessions:
            merged_sessions.append(current)
            continue
        previous = merged_sessions[-1]
        if current["start"] <= (previous["end"] + merge_threshold_seconds):
            previous["end"] = max(previous["end"], current["end"])
            previous["speakers"].extend(current["speakers"])
        else:
            merged_sessions.append(current)
    merged_sessions.sort(key=lambda x: x["end"] - x["start"], reverse=True)
    if len(merged_sessions) < 2:
        print("Warning: Could not isolate two distinct conversations safely. Proceeding with best estimate...")
    final_2_conversations = merged_sessions[:2]
    final_2_conversations.sort(key=lambda x: x["start"])
    results = {}
    for i, conv in enumerate(final_2_conversations):
        start_anchor = conv["start"]
        for b in staff_timeline:
            if b["start"] >= (conv["start"] - 45) and b["end"] <= conv["start"]:
                start_anchor = min(start_anchor, b["start"])
        end_anchor = conv["end"]
        for b in staff_timeline:
            if b["start"] >= conv["end"] and b["start"] <= (conv["end"] + 30):
                end_anchor = max(end_anchor, b["end"])
        results[f"Conversation {i+1}"] = {"start": start_anchor, "end": end_anchor}
    return results



if __name__ == "__main__":
    import glob
    import os
    import json
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    audio_dir = os.path.join(base_path, "audio")
    audio_files = glob.glob(os.path.join(audio_dir, "*.mp3"))
    
    evaluation_results = {}
    
    for audio_file in audio_files:
        filename = os.path.basename(audio_file)
        print("\n" + "="*70)
        print(f"PROCESSING EXTERNAL AUDIO FILE: {audio_file}")
        print("="*70)
        try:
            raw_transcript = get_transcript_data(audio_file)
            boundaries = analyze_sessions(raw_transcript)
            
            file_eval = {}
            if boundaries:
                for conv, times in boundaries.items():
                    file_eval[conv] = {
                        "start": round(times['start'], 2),
                        "end": round(times['end'], 2)
                    }
            evaluation_results[filename] = file_eval
            print(f"-> Successfully processed {filename}")
        except Exception as e:
            print(f"Pipeline Error on {filename}: {e}")
            
    print("\n" + "=" * 52)
    print("EVALUATION OUTPUT (JSON FORMAT)")
    print("=" * 52)
    print(json.dumps(evaluation_results, indent=2))
