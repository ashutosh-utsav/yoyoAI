# Sarvam AI + GPT-4o Speaker Extraction

This approach uses Sarvam AI's batch STT service, which natively handles Indian languages (Kannada, Hindi, etc.) alongside built-in diarization. The resulting speaker-identified transcript is then fed to OpenAI's GPT-4o to label each unique speaker as 'Staff', 'Customer', or 'Background', allowing the script to logically extract chronological conversation timestamps.


Given how badly Pyannote choked on the codemixing, I pivoted aggressively. I thought, what if we use Sarvam AI which is built literally for this? Probably this might work.

I found out Sarvam Batch STT, which gives me much better transcribed Kannada and Hindi. Then I am using GPT-4o to label the roles. My central thesis here was that perfect Indian STT instantly solves the boundary problem.

The primary hurdle with Sarvam is getting the language code right. However, it still drops the ball on chaotic overlapping background chatter. in a noisy store. It is working very average, but noticeably better than pure Pyannote. 

I invested heavily in testing this because Sarvam handles the codemixing seamlessly. 

Looking at the metric dumps, my takeaway is that it's failing because even with amazing STT, the 5-minute billing pauses and overlapping chaos still confuse the LLM into splitting one customer into two. So this didn't entirely work flawlessly.
