# Dual-Step LLM Approach

This approach uses Pyannote for traditional Speech-to-Text and Diarization. Once the transcript is generated, it formats the result into a human-readable script and forwards it to OpenAI's GPT-4o for semantic reasoning to determine the precise start and end of the customer interactions based on context.
