# Sarvam AI + GPT-4o Speaker Extraction

This approach uses Sarvam AI's batch STT service, which natively handles Indian languages (Kannada, Hindi, etc.) alongside built-in diarization. The resulting speaker-identified transcript is then fed to OpenAI's GPT-4o to label each unique speaker as 'Staff', 'Customer', or 'Background', allowing the script to logically extract chronological conversation timestamps.
