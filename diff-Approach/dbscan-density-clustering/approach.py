import os
import time
import numpy as np
from dotenv import load_dotenv
from pyannoteai.sdk import Client
from sklearn.cluster import DBSCAN

load_dotenv()

API_KEY = os.getenv("PYANNOTE_API_KEY")
client = Client(API_KEY)

def get_transcript_data(audio_path):
    print(f"Uploading {audio_path}...")
    media_url = client.upload(audio_path)
    job_id = client.diarize(media_url, model="precision-2") 
    print("Processing STT + Diarization...")
    while True:
        job = client.retrieve(job_id)
        if job["status"] == "succeeded":
            return job["output"]["diarization"]
        elif job["status"] in ["failed", "canceled"]:
            raise Exception("Job failed.")
        time.sleep(5)


def get_core_conversation_window(timestamps, eps=60, min_samples=3):
    """
    Uses DBSCAN to find the densest cluster of speech and drop outlier noise.
    eps=60: If a speaker goes silent for >60 seconds, the cluster breaks.
    """
    if len(timestamps) < min_samples:
        return min(timestamps), max(timestamps)
    X = np.array(timestamps).reshape(-1, 1)
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    labels = db.labels_
    unique_labels = set(labels)
    if -1 in unique_labels:
        unique_labels.remove(-1)
    if not unique_labels:
        return min(timestamps), max(timestamps)
    largest_cluster = max(unique_labels, key=lambda l: list(labels).count(l))
    core_timestamps = [timestamps[i] for i in range(len(timestamps)) if labels[i] == largest_cluster]
    return min(core_timestamps), max(core_timestamps)


def find_boundaries_via_density(timeline):
    print("\nExecuting Density-Based Anomaly Detection...")
    speaker_times = {}
    for block in timeline:
        spk = block["speaker"]
        if spk not in speaker_times:
            speaker_times[spk] = []
        speaker_times[spk].append((block["start"] + block["end"]) / 2.0)
    valid_speakers = []
    for spk, times in speaker_times.items():
        if len(times) > 5:
            valid_speakers.append((spk, len(times)))
    valid_speakers.sort(key=lambda x: x[1], reverse=True)
    main_staff = valid_speakers[0][0]
    cust_1 = valid_speakers[1][0]
    cust_2 = valid_speakers[2][0]
    print(f"Roles Identified -> Staff: {main_staff}, Cust 1: {cust_1}, Cust 2: {cust_2}")
    c1_start, c1_end = get_core_conversation_window(speaker_times[cust_1])
    c2_start, c2_end = get_core_conversation_window(speaker_times[cust_2])
    if c2_start < c1_start:
        c1_start, c1_end, c2_start, c2_end = c2_start, c2_end, c1_start, c1_end
        cust_1, cust_2 = cust_2, cust_1
    staff_times = [t for t in speaker_times[main_staff]]
    conv1_actual_start = min([t for t in staff_times if t <= c1_start and c1_start - t < 30] + [c1_start])
    conv2_actual_start = min([t for t in staff_times if t <= c2_start and t > c1_end and c2_start - t < 30] + [c2_start])
    return {
        "Conversation 1": {"start": conv1_actual_start, "end": c1_end},
        "Conversation 2": {"start": conv2_actual_start, "end": c2_end}
    }



if __name__ == "__main__":
    audio_file = "audio/Sample1KN.mp3" 
    raw_timeline = get_transcript_data(audio_file)
    boundaries = find_boundaries_via_density(raw_timeline)
    print("\n" + "="*40)
    print("FINAL CONVERSATION BOUNDARIES")
    print("="*40)
    def format_time(seconds):
        return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
    for conv, times in boundaries.items():
        print(f"{conv}: [ {format_time(times['start'])} --> {format_time(times['end'])} ]")