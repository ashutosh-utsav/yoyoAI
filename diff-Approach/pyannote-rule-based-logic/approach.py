import os
import time
from dotenv import load_dotenv
from pyannoteai.sdk import Client

load_dotenv()

API_KEY = os.getenv("PYANNOTE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found. Please check your .env file.")
client = Client(API_KEY)

def get_diarization_data(audio_path):
    """Uploads the file and returns the Pyannote timeline data."""
    print(f"Uploading {audio_path}...")
    media_url = client.upload(audio_path)
    print("Processing... This might take a minute.")
    job_id = client.diarize(media_url, model="precision-2")
    while True:
        job = client.retrieve(job_id)
        if job["status"] == "succeeded":
            return job["output"]["diarization"]
        elif job["status"] in ["failed", "canceled"]:
            raise Exception("Job failed.")
        time.sleep(5)


def find_conversation_boundaries(timeline):
    """
    Analyzes the timeline to find Staff, Customers, and Conversation boundaries.
    """
    speaker_stats = {}
    for block in timeline:
        spk = block["speaker"]
        duration = block["end"] - block["start"]
        if spk not in speaker_stats:
            speaker_stats[spk] = {
                "total_time": 0.0, 
                "turns": 0, 
                "first_seen": block["start"], 
                "last_seen": block["end"]
            }
        speaker_stats[spk]["total_time"] += duration
        speaker_stats[spk]["turns"] += 1
        speaker_stats[spk]["last_seen"] = block["end"]
    valid_speakers = []
    for spk, stats in speaker_stats.items():
        if stats["turns"] > 5 and stats["total_time"] > 10.0:
            valid_speakers.append((spk, stats))
    valid_speakers.sort(key=lambda x: x[1]["total_time"], reverse=True)
    main_staff = valid_speakers[0][0]
    customers = [valid_speakers[1], valid_speakers[2]]
    customers.sort(key=lambda x: x[1]["first_seen"])
    cust_1 = customers[0][0]
    cust_2 = customers[1][0]
    print(f"Identified Roles -> Staff: {main_staff}, Cust 1: {cust_1}, Cust 2: {cust_2}")
    conv1_start = speaker_stats[cust_1]["first_seen"]
    for block in timeline:
        if block["speaker"] == main_staff and block["start"] < conv1_start:
            if conv1_start - block["end"] < 30.0:
                conv1_start = block["start"]
                break
    conv1_end = speaker_stats[cust_1]["last_seen"]
    conv2_start = speaker_stats[cust_2]["first_seen"]
    for block in timeline:
        if block["speaker"] == main_staff and block["end"] > conv1_end and block["start"] < conv2_start:
             if conv2_start - block["end"] < 30.0:
                 conv2_start = block["start"]
                 break
    conv2_end = speaker_stats[cust_2]["last_seen"]
    return {
        "Conversation 1": {"start": conv1_start, "end": conv1_end},
        "Conversation 2": {"start": conv2_start, "end": conv2_end}
    }


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
            raw_timeline = get_diarization_data(audio_file)
            boundaries = find_conversation_boundaries(raw_timeline)
            
            file_eval = {}
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
