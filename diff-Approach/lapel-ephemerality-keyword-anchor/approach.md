# Lapel Protocol: Ephemerality Filtering & Anchoring

This is an advanced heuristics approach tailored specifically for lapel microphone data. First, it identifies the staff member and then aggressively filters out "permanent" background colleagues by dropping anyone who speaks across a majority (e.g., >65%) of the audio's duration, retaining only "ephemeral" short-lived customers. Finally, it searches near the customer's identified blocks for specific greeting and farewell keywords by the staff member to perfectly anchor the start and end of the interaction.


So basically, this approach came to my mind. What I am thinking right now is what if we look at the constraints of the physical lapel microphone? The salesman wears it the whole time, so what if we filter out colleagues because they speak ephemerally? Probably this might work.

I found out we can just anchor boundaries using words like 'hello' and 'thank you'. The basic assumption I am making here is that every transaction starts and ends cleanly with these keywords. 

The important thing with this protocol is catching those exact keywords. The problem is not very accurate; customers don't always say formal greetings in a real noisy store! It's failing multiple times. It is working very average.

Why I thought this can be an option is it logically mimics how human brains detect a new customer interaction in retail. 

My recent thought process is that it's failing because people are too unpredictable and overlapping. The real world doesn't follow strict greeting protocols. I checked with all three audio, and apart from one English file, both the Kannada audio were failing exponentially on keyword bounds.
