# Pure Pyannote Rule-Based Logic

A purely rule-based approach driven by Pyannote diarization statistics. It calculates the total talk time, total turns, and first/last seen timestamps per individual speaker inside the timeline to identify the main staff member and the primary customers. It then scans for the staff member's utterances immediately preceding and succeeding the customer's speaking blocks to rigidly derive the boundaries of the transaction.
