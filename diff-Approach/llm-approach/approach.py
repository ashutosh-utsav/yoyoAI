import os
import time
import json
from dotenv import load_dotenv
from pyannoteai.sdk import Client
from openai import OpenAI
load_dotenv()
PYANNOTE_KEY = os.getenv("PYANNOTE_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not PYANNOTE_KEY or not OPENAI_KEY:
    raise ValueError("Missing API Keys. Check your .env file.")
pyannote_client = Client(PYANNOTE_KEY)
openai_client = OpenAI(api_key=OPENAI_KEY)
def get_transcript_data(audio_path):
    print(f"\n[1/3] Uploading {audio_path} to Pyannote...")
    media_url = pyannote_client.upload(audio_path)
    print("[2/3] Processing STT + Diarization (This takes a moment)...")
    job_id = pyannote_client.diarize(media_url, model="precision-2", transcription=True)
    while True:
        job = pyannote_client.retrieve(job_id)
        if job["status"] == "succeeded":
            return job["output"]["turnLevelTranscription"]
        elif job["status"] in ["failed", "canceled"]:
            raise Exception("Pyannote API Job failed.")
        time.sleep(5)
def analyze_with_openai(transcript_json):
    print("[3/3] Passing transcript to OpenAI for semantic boundary extraction...")
    script_text = ""
    for block in transcript_json:
        start_fmt = f"{int(block['start'] // 60):02d}:{int(block['start'] % 60):02d}"
        end_fmt = f"{int(block['end'] // 60):02d}:{int(block['end'] % 60):02d}"
        script_text += f"[{start_fmt} - {end_fmt}] {block['speaker']}: {block['text']}\n"
    system_prompt = """
    You are an elite retail analytics AI. You are analyzing a diarized transcript from a lapel microphone worn by a retail salesman in an Indian store.
    ENVIRONMENTAL REALITY:
    1. The salesman wears the mic and speaks the most.
    2. The salesman often chats with colleagues/friends in the background (idle banter). Ignore this.
    3. Customers walk up, ask specific product questions (sizes, prices, availability, queries), transact, and leave. 
    4. NO IDEAL CONDITIONS: Customers RARELY say "Hello" or "Goodbye". They usually start abruptly (e.g., "Do you have this?", "Show me that") and leave abruptly.
    5. BILLING PAUSES: There are often long silences (2 to 5 minutes) while the salesman bills the item or grabs inventory. DO NOT break a single customer conversation into two just because of a pause. Look at the semantic continuity.
    6. COUPLES: A single customer interaction might involve two people (e.g., a husband and wife) talking to the salesman. Group them together as one conversation block.
    YOUR TASK:
    Read the transcript, understand the context of the interactions, and extract the exact Start and End timestamps for the TWO distinct customer interactions. 
    Output ONLY a valid, raw JSON object in this exact format. Do not include markdown formatting (like ```json), and do not include any explanations.
    {
      "Conversation_1": {"start": "MM:SS", "end": "MM:SS"},
      "Conversation_2": {"start": "MM:SS", "end": "MM:SS"}
    }
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the transcript:\n\n{script_text}"}
        ],
        temperature=0.1
    )
    raw_output = response.choices[0].message.content.strip()
    if raw_output.startswith("```json"):
        raw_output = raw_output[7:]
    if raw_output.endswith("```"):
        raw_output = raw_output[:-3]
    try:
        return json.loads(raw_output.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM output: {raw_output}")
        raise e
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
            final_boundaries = analyze_with_openai(raw_transcript)
            
            file_eval = {}
            def parse_mmss(time_str):
                try:
                    if isinstance(time_str, float) or isinstance(time_str, int):
                        return float(time_str)
                    parts = str(time_str).split(":")
                    if len(parts) == 2:
                        return float(parts[0]) * 60 + float(parts[1])
                    elif len(parts) == 3:
                        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    pass
                return 0.0
                
            if isinstance(final_boundaries, dict):
                for conv, times in final_boundaries.items():
                    if isinstance(times, dict) and 'start' in times and 'end' in times:
                        file_eval[conv.replace("_", " ")] = {
                            "start": round(parse_mmss(times['start']), 2),
                            "end": round(parse_mmss(times['end']), 2)
                        }
            evaluation_results[filename] = file_eval
            print(f"-> Successfully processed {filename}")
        except Exception as e:
            print(f"Pipeline Error on {filename}: {e}")
            
    print("\n" + "=" * 52)
    print("EVALUATION OUTPUT (JSON FORMAT)")
    print("=" * 52)
    print(json.dumps(evaluation_results, indent=2))
