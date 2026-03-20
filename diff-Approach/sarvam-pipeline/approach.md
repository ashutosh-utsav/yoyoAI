# Sarvam AI + GPT-4o Speaker Extraction

This approach uses Sarvam AI's batch STT service, which natively handles Indian languages (Kannada, Hindi, etc.) alongside built-in diarization. The resulting speaker-identified transcript is then fed to OpenAI's GPT-4o to label each unique speaker as 'Staff', 'Customer', or 'Background', allowing the script to logically extract chronological conversation timestamps.


So basically, this approach came to my mind. Pyannote was struggling so hard with Indian languages, so what if we use Sarvam AI which is built literally for this? Probably this might work.

I found out Sarvam Batch STT, which gives me much better transcribed Kannada and Hindi. Then I am using GPT-4o to label the roles. The basic assumption I am making here is that perfect Indian STT instantly solves the boundary problem.

The important thing with Sarvam is getting the language code right. The problem is it's still missing some of the deep background speech in a noisy store. It is working very average, but noticeably better than pure Pyannote. 

Why I thought this can be an option is that Sarvam handles the codemixing seamlessly. 

My recent thought process is that it's failing because even with amazing STT, the 5-minute billing pauses and overlapping chaos still confuse the LLM into splitting one customer into two. So this didn't entirely work flawlessly.
