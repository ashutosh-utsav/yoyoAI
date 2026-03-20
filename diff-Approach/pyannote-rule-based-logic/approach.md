# Pure Pyannote Rule-Based Logic

A purely rule-based approach driven by Pyannote diarization statistics. It calculates the total talk time, total turns, and first/last seen timestamps per individual speaker inside the timeline to identify the main staff member and the primary customers. It then scans for the staff member's utterances immediately preceding and succeeding the customer's speaking blocks to rigidly derive the boundaries of the transaction.


I wanted to try something extremely barebones. I thought: what if we just stick to strict statistics from Pyannote without any fancy LLMs? Probably this might work.

I am just counting who speaks the most and assigning that as the staff, then trying to mathematically find the next two. The statistical gamble I took was that the customer speaks the second and third most amount of time.

The trickiest part of this rule-based logic is the time thresholds we hardcode. Right now I put some strict gaps to separate them. Sadly, this rigidity causes extreme failure states. it violently fails if there is overlap or if a colleague speaks too much and steals the second-most speaking spot. It is working very average.

The massive appeal of this direction was that it is cheap and incredibly fast since it doesn't need LLM calls. 

My final verdict on this iteration is that the real world is too messy for hardcoded if-else rules. A customer might speak very little while a colleague chatters away. I checked with all three audio, and it was failing exponentially.
