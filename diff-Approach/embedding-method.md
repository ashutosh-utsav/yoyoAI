# Semantic Vector Embeddings

This approach identifies boundaries by evaluating semantic meaning. Using Pyannote for transcription, it computes sentence embeddings for rolling windows of text via `paraphrase-multilingual-MiniLM-L12-v2`. It then calculates the cosine similarity between adjacent text blocks; a significant drop in similarity indicates a drastic shift in topic, marking the transition from one customer conversation to the next.
