# Deterministic Session Merging

This represents a robust deterministic approach executed post-Pyannote transcription. It evaluates all the identified "customer" interactions and evaluates their proximities. It then forcefully merges any distinct customer speaking blocks that occur closely together (e.g., within a 180-second threshold) to account for mid-transaction silences, seamlessly returning the two largest chronological conversation blocks.


So basically, this approach came to my mind. What if we just look at the customer blocks and merge them if they happen within a few minutes of each other? Probably this might work.

I am literally just taking timestamps and gluing them together if the gap is less than a certain threshold. The basic assumption I am making here is that a customer never goes silent for longer than this fixed amount of time.

The important thing with session merging is finding that magic threshold number, like 240 seconds. The problem is not very accurate; if a customer browses silently for 5 minutes, it randomly splits them into two people! It is working very average.

Why I thought this can be an option is it natively handles short pauses well mathematically. 

My recent thought process is that the 240 second threshold is completely arbitrary and real life doesn't obey rules like that. I checked with all three audio, and it's failing because the pauses are totally unpredictable. This approach can work if the audio is very tailored, but dealing with real audio, so this didn't work.
