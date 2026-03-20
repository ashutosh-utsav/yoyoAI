# Pure Pyannote Rule-Based Logic

A purely rule-based approach driven by Pyannote diarization statistics. It calculates the total talk time, total turns, and first/last seen timestamps per individual speaker inside the timeline to identify the main staff member and the primary customers. It then scans for the staff member's utterances immediately preceding and succeeding the customer's speaking blocks to rigidly derive the boundaries of the transaction.


So basically, this approach came to my mind. What if we just stick to strict statistics from Pyannote without any fancy LLMs? Probably this might work.

I am just counting who speaks the most and assigning that as the staff, then trying to mathematically find the next two. The basic assumption I am making here is that the customer speaks the second and third most amount of time.

The important thing with this rule-based logic is the time thresholds we hardcode. Right now I put some strict gaps to separate them. The problem is not very accurate; it violently fails if there is overlap or if a colleague speaks too much and steals the second-most speaking spot. It is working very average.

Why I thought this can be an option is that it is cheap and incredibly fast since it doesn't need LLM calls. 

My recent thought process is that the real world is too messy for hardcoded if-else rules. A customer might speak very little while a colleague chatters away. I checked with all three audio, and it was failing exponentially.
