# Semantic Vector Embeddings

This approach identifies boundaries by evaluating semantic meaning. Using Pyannote for transcription, it computes sentence embeddings for rolling windows of text via `paraphrase-multilingual-MiniLM-L12-v2`. It then calculates the cosine similarity between adjacent text blocks; a significant drop in similarity indicates a drastic shift in topic, marking the transition from one customer conversation to the next.


So basically, this approach came to my mind. What I am thinking right now is what if we check the meaning of the sentences instead of just who is speaking? Probably this might work.

I found out sentence embeddings, which basically groups the distinct topics. I am using sentence transformers to check the vector similarity between blocks. The basic assumption I am making here is that when a new customer comes, the topic completely shifts. 

The important thing with embeddings is finding the right similarity threshold and window size. Right now it's just looking for big drops, but I have tested with different window sizes also. The problem is not very accurate; people don't shift topics cleanly in a retail store, they jump back and forth. It is working very average, very average.

Why I thought this can be an option is that we could capture the actual conversation flow without hardcoded rules. 

My recent thought process is that the context is missing, it's failing because customers jump back and forth on topics and the embeddings get confused. This approach can work if the audio is very tailored, but I go there dealing with real audio and overlapping voices, so this didn't work. I checked with all three audio, and it was failing exponentially.
