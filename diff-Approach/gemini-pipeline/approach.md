# Gemini Native Audio Pipeline

This approach uploads the entire audio natively to Gemini's 2.5 Flash model, which supports multimodal audio processing. It bypasses traditional Speech-to-Text (STT) and diarization altogether, relying on the model to 'listen' directly to the audio file and return the exact customer conversation start and end boundaries using an LLM prompt.
