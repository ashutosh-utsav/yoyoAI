import os
import time
import numpy as np
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from pyannoteai.sdk import Client
load_dotenv()
API_KEY = os.getenv("PYANNOTE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found. Please check your .env file.")
client = Client(API_KEY)
print("Loading multilingual embedding model... (This runs locally)")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
def get_transcript_data(audio_path):
    """Uploads the file and returns the speaker-attributed transcript."""
    print(f"\nUploading {audio_path} to pyannoteAI...")
    media_url = client.upload(audio_path)
    print("Processing STT + Diarization... This might take a minute.")
    job_id = client.diarize(media_url, model="precision-2", transcription=True)
    while True:
        job = client.retrieve(job_id)
        if job["status"] == "succeeded":
            return job["output"]["turnLevelTranscription"]
        elif job["status"] in ["failed", "canceled"]:
            raise Exception("Job failed.")
        print("Polling API... waiting 5 seconds.")
        time.sleep(5)
def find_semantic_boundaries(transcript_blocks, window_size=3):
    """
    Finds the conversation split by calculating cosine similarity between 
    rolling windows of text embeddings.
    """
    print("\nExecuting Semantic Vector Analysis...")
    texts = [block["text"] for block in transcript_blocks]
    embeddings = embedding_model.encode(texts)
    similarities = []
    split_points = []
    for i in range(len(embeddings) - 2 * window_size):
        window_a_vector = np.mean(embeddings[i : i + window_size], axis=0).reshape(1, -1)
        window_b_vector = np.mean(embeddings[i + window_size : i + 2 * window_size], axis=0).reshape(1, -1)
        sim_score = cosine_similarity(window_a_vector, window_b_vector)[0][0]
        split_index = i + window_size - 1
        similarities.append(sim_score)
        split_points.append(split_index)
    min_sim_index = np.argmin(similarities)
    boundary_block_index = split_points[min_sim_index]
    conv1_start = transcript_blocks[0]["start"]
    conv1_end = transcript_blocks[boundary_block_index]["end"]
    conv2_start = transcript_blocks[boundary_block_index + 1]["start"]
    conv2_end = transcript_blocks[-1]["end"]
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
            raw_transcript = get_transcript_data(audio_file)
            boundaries = find_semantic_boundaries(raw_transcript, window_size=2)
            
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
