# YoyoAI Audio Analytics Laboratory

This repository is dedicated to an ongoing experimental matrix designed to extract precise start and end conversation boundaries from continuous, noisy lapel-microphone recordings captured in Indian retail environments. 

The core challenge involves navigating codemixed languages, erratic background noise, unpredictable overlapping conversations, and exceptionally long billing pauses (e.g., 5 minutes of silence in the middle of a customer interaction).

---

## 📂 Folder Structure

The repository is modularized into three core components:

### 1. `audio/`
Houses the raw `.mp3` source files used for testing and inference. These include samples in Kannada (`KN`) and English/Codemixed (`EN`).

### 2. `diff-Approach/`
An archive of 8 different experimental methodologies developed during the iterative phase. Each folder contains:
- `approach.md`: A raw, honest developmental reflection on what the approach is, its core assumptions, where it worked, and why it ultimately failed on real-world edge cases.
- `approach.py`: The autonomous script executing the methodology dynamically against all files in `audio/`.
Some featured experiments include *DBSCAN Density Clustering*, *Lapel Ephemerality Anchoring*, and *Sarvam AI + GPT-4o Labeling*.

### 3. `Final-approach/`
The finally adopted approach.
- Driven by `main.py` and documented in `approach.md`.
- Relies on aggressive **Local Voice Activity Detection (VAD)** compression (using `pydub`) to mathematically remove all dead silences and billing pauses into a tracked ledger.
- This compressed payload is natively processed via Gemini 2.5 Flash multimodality, preventing LLM context hallucination and effortlessly managing codemixed audio without fragile intermediate STT engines.

### 4. `evolution and matrix/`
A rigorous evaluation engine designed to empirically chart the success of any experimental paradigm.
- **`ground_truth.json`**: Hand-annotated baseline timestamps for accuracy parity.
- **`evaluate_approach.py`**: A universally compatible Python tester that calculates Mean Absolute Errors (Seconds) and Intersection-Over-Union (IoU) scores.

---

## 🛠 Setup & Installation

1. Install Python 3.10+ and the `uv` package manager.
2. Clone this repository.
3. Establish your environment variables:
   ```bash
   cp .env.example .env
   ```
4. Populate your `.env` securely with your active Google Gemini, OpenAI, Pyannote, and Sarvam API keys.

---

## 🚀 Usage Guide

### Running an Approach Manually
Every approach autonomously iterates over the `audio/` directory. You can run any of them natively using `uv`:

```bash
uv run diff-Approach/gemini-pipeline/approach.py
uv run Final-approach/main.py
```

All 9 scripts have been standardized to conclude with an identical `EVALUATION OUTPUT` JSON dump mimicking the structure of the ground truth.

### The Evolution and Matrix Engine
To objectively mathematically rank how an approach performed, pass any script to the `evaluate_approach.py` engine. 

```bash
uv run "evolution and matrix/evaluate_approach.py" diff-Approach/lapel-ephemerality-keyword-anchor/approach.py
```

**How the Evaluation Works:**
1. **Execution**: It dynamically executes the target approach script sequentially against all core audio files.
2. **Standardized Extraction**: It intercepts the standardized JSON output dump (`EVALUATION OUTPUT`) that all valid approaches are programmed to emit.
3. **Metric Calculations**: It strictly cross-references the predicted timestamps against `ground_truth.json` to calculate:
   - **Intersection Over Union (IoU)**: A score exactly between 0.0 and 1.0 indicating overlap. It is calculated by dividing the overlapping duration of the predicted and true conversation bounds (Intersection) by the total duration of both bounding windows combined (Union).
   - **Start_Error_sec**: The absolute mathematical difference in seconds between the Ground Truth Start and Predicted Start.
   - **End_Error_sec**: The absolute mathematical difference in seconds between the Ground Truth End and Predicted End.
4. **Console Visualization**: It prints a granular breakdown of how the model performed on *Conversation 1* vs. *Conversation 2* for every single audio file, accompanied by a global mean score.
5. **JSON Archival**: It outputs the aggregated analysis into a persistent JSON report (e.g., `lapel-ephemerality-keyword-anchor_metrics.json`) situated inside the `evolution and matrix/` directory for historical tracking.
