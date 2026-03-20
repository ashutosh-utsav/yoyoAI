# Deterministic Session Merging

This represents a robust deterministic approach executed post-Pyannote transcription. It evaluates all the identified "customer" interactions and evaluates their proximities. It then forcefully merges any distinct customer speaking blocks that occur closely together (e.g., within a 180-second threshold) to account for mid-transaction silences, seamlessly returning the two largest chronological conversation blocks.


I brainstormed a purely numerical clustering idea. What if we just look at the customer blocks and merge them if they happen within a few minutes of each other? Probably this might work.

I am literally just taking timestamps and gluing them together if the gap is less than a certain threshold. The fragile assumption baking into the code was that a customer never goes silent for longer than this fixed amount of time.

The defining lever of session merging is finding that magic threshold number, like 240 seconds. The real-life accuracy is unfortunately terrible. if a customer browses silently for 5 minutes, it randomly splits them into two people! It is working very average.

I was originally drawn to this model because it natively handles short pauses well mathematically. 

The hard lesson learned from the edge cases is that the 240 second threshold is completely arbitrary and real life doesn't obey rules like that. I checked with all three audio, and it's failing because the pauses are totally unpredictable. This approach can work if the audio is very tailored, but dealing with real audio, so this didn't work.
