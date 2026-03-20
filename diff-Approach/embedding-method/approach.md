# Semantic Vector Embeddings

This approach identifies boundaries by evaluating semantic meaning. Using Pyannote for transcription, it computes sentence embeddings for rolling windows of text via `paraphrase-multilingual-MiniLM-L12-v2`. It then calculates the cosine similarity between adjacent text blocks; a significant drop in similarity indicates a drastic shift in topic, marking the transition from one customer conversation to the next.


My initial train of thought leading here was: what if we check the meaning of the sentences instead of just who is speaking? Probably this might work.

I found out sentence embeddings, which basically groups the distinct topics. I am using sentence transformers to check the vector similarity between blocks. The core hypothesis driving this attempt was that when a new customer comes, the topic completely shifts. 

The critical factor when deploying embeddings is finding the right similarity threshold and window size. Right now it's just looking for big drops, but I have tested with different window sizes also. Unfortunately, the precision isn't there. people don't shift topics cleanly in a retail store, they jump back and forth. It is working very average, very average.

The reason I fundamentally believed this could crack the case is that we could capture the actual conversation flow without hardcoded rules. 

Looking back, my main realization is that the context is missing, it's failing because customers jump back and forth on topics and the embeddings get confused. This approach can work if the audio is very tailored, but I go there dealing with real audio and overlapping voices, so this didn't work. I checked with all three audio, and it was failing exponentially.
