# Deterministic Session Merging

This represents a robust deterministic approach executed post-Pyannote transcription. It evaluates all the identified "customer" interactions and evaluates their proximities. It then forcefully merges any distinct customer speaking blocks that occur closely together (e.g., within a 180-second threshold) to account for mid-transaction silences, seamlessly returning the two largest chronological conversation blocks.
