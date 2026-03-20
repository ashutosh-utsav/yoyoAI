import os
import json
import time
import tempfile
from dotenv import load_dotenv
from sarvamai import SarvamAI
from openai import OpenAI
load_dotenv()
SARVAM_KEY = os.getenv("SARVAM_AI_API")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not SARVAM_KEY or not OPENAI_KEY:
    raise ValueError("Missing API keys. Check SARVAM_AI_API and OPENAI_API_KEY in .env")
sarvam_client = SarvamAI(api_subscription_key=SARVAM_KEY)
openai_client = OpenAI(api_key=OPENAI_KEY)
def get_diarized_transcript(audio_path, language_code="kn-IN", num_speakers=5):
    """
    Submits audio to Sarvam's Batch STT API with native diarization.
    Returns a list of entries: { speaker_id, transcript, start_time_seconds, end_time_seconds }
    Set language_code to:
      - "kn-IN" for Kannada
      - "hi-IN" for Hindi
      - "en-IN" for English
      - "auto" for automatic detection (recommended for codemixed audio)
    """
    print(f"\n[1/3] Submitting '{audio_path}' to Sarvam Batch STT...")
    print(f"      Model: saaras:v3 | Language: {language_code} | Speakers: ~{num_speakers}")
    job = sarvam_client.speech_to_text_job.create_job(
        model="saaras:v3",
        mode="transcribe",
        language_code=language_code,
        with_diarization=True,
        num_speakers=num_speakers
    )
    print("      Uploading audio file...")
    job.upload_files(file_paths=[audio_path])
    job.start()
    print("      Processing... (waiting for Sarvam to complete the job)")
    job.wait_until_complete()
    with tempfile.TemporaryDirectory() as tmp_dir:
        job.download_outputs(output_dir=tmp_dir)
        result_file = None
        for fname in os.listdir(tmp_dir):
            if fname.endswith(".json"):
                result_file = os.path.join(tmp_dir, fname)
                break
        if not result_file:
            raise FileNotFoundError("Sarvam did not return a JSON output file.")
        with open(result_file, "r", encoding="utf-8") as f:
            raw_output = json.load(f)
    entries = raw_output.get("diarized_transcript", {}).get("entries", [])
    if not entries:
        raise ValueError("Sarvam returned no diarized transcript entries. Check language_code or audio quality.")
    print(f"      Got {len(entries)} diarized segments across the audio.")
    return entries
def label_speakers_with_openai(entries):
    """
    Sends the diarized transcript to GPT-4o.
    GPT-4o identifies which speaker_id is STAFF, CUSTOMER_1, CUSTOMER_2, BACKGROUND.
    Returns a dict mapping speaker_id → role.
    """
    print("\n[2/3] Passing transcript to GPT-4o for speaker role identification...")
    unique_speakers = sorted(set(e["speaker_id"] for e in entries))
    print(f"      Unique speakers detected by Sarvam: {unique_speakers}")
    script_text = ""
    for e in entries:
        start = e["start_time_seconds"]
        end   = e["end_time_seconds"]
        start_fmt = f"{int(start // 60):02d}:{int(start % 60):02d}"
        end_fmt   = f"{int(end   // 60):02d}:{int(end   % 60):02d}"
        script_text += f"[{start_fmt}-{end_fmt}] Speaker {e['speaker_id']}: {e['transcript']}\n"
    system_prompt = """
You are an expert retail conversation analyst. You are given a diarized transcript from a lapel microphone worn by a salesman in an Indian retail store. The audio is in Kannada, Hindi, English, or a mix.
RULES ABOUT THIS SPECIFIC RECORDING:
1. The SALESMAN wears the mic and speaks the MOST — usually across the full audio duration.
2. Two distinct CUSTOMERS visit the store in sequence. Each customer asks about products, gets helped, and leaves.
3. There are BACKGROUND FRIENDS or COLLEAGUES of the salesman scattered throughout. They banter casually and appear across the whole recording (not just in one window).
4. BILLING PAUSES of 2-5 minutes happen mid-transaction. Do NOT split a single customer visit into two because of silence.
5. Customers do NOT use formal greetings. They start with product queries like "do you have this?", "how much?", show me XYZ.
YOUR TASK:
Assign each unique speaker_id exactly one role from: STAFF, CUSTOMER_1, CUSTOMER_2, BACKGROUND.
- STAFF = speaks most, present throughout
- CUSTOMER_1 = first customer to appear
- CUSTOMER_2 = second customer to appear  
- BACKGROUND = colleague/friend present throughout (NOT a customer)
If there are more speaker IDs than roles, assign the extra ones to BACKGROUND.
Output ONLY a valid raw JSON object like this. No markdown, no explanation:
{
  "0": "STAFF",
  "1": "CUSTOMER_1",
  "2": "CUSTOMER_2",
  "3": "BACKGROUND"
}
"""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the diarized transcript:\n\n{script_text}"}
        ],
        temperature=0.1
    )
    raw_output = response.choices[0].message.content.strip()
    if raw_output.startswith("```json"):
        raw_output = raw_output[7:]
    if raw_output.startswith("```"):
        raw_output = raw_output[3:]
    if raw_output.endswith("```"):
        raw_output = raw_output[:-3]
    speaker_labels = json.loads(raw_output.strip())
    print(f"      GPT-4o Speaker Labels: {speaker_labels}")
    return speaker_labels
def compute_boundaries(entries, speaker_labels):
    """
    Pure Python: groups segments by role, returns min/max timestamps per conversation.
    No guessing, no thresholds — the LLM did the hard work above.
    """
    print("\n[3/3] Computing final conversation boundaries from labels...")
    grouped = {"CUSTOMER_1": [], "CUSTOMER_2": []}
    for e in entries:
        role = speaker_labels.get(str(e["speaker_id"]), "BACKGROUND")
        if role in grouped:
            grouped[role].append(e)
    results = {}
    for i, role in enumerate(["CUSTOMER_1", "CUSTOMER_2"], start=1):
        segs = grouped[role]
        if not segs:
            print(f"      Warning: No segments found for {role}")
            continue
        conv_start = min(s["start_time_seconds"] for s in segs)
        conv_end   = max(s["end_time_seconds"]   for s in segs)
        results[f"Conversation {i}"] = {"start": conv_start, "end": conv_end}
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
        
        if "KN" in filename.upper() or "KANNADA" in filename.upper():
            language_code = "kn-IN"
        elif "HI" in filename.upper() or "HINDI" in filename.upper():
            language_code = "hi-IN"
        else:
            language_code = "en-IN"

        try:
            entries         = get_diarized_transcript(audio_file, language_code)
            speaker_labels  = label_speakers_with_openai(entries)
            boundaries      = compute_boundaries(entries, speaker_labels)
            
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
