# Lapel Protocol: Ephemerality Filtering & Anchoring

This is an advanced heuristics approach tailored specifically for lapel microphone data. First, it identifies the staff member and then aggressively filters out "permanent" background colleagues by dropping anyone who speaks across a majority (e.g., >65%) of the audio's duration, retaining only "ephemeral" short-lived customers. Finally, it searches near the customer's identified blocks for specific greeting and farewell keywords by the staff member to perfectly anchor the start and end of the interaction.


I decided to tackle it from a completely physical angle. I started wondering: what if we look at the constraints of the physical lapel microphone? The salesman wears it the whole time, so what if we filter out colleagues because they speak ephemerally? Probably this might work.

I found out we can just anchor boundaries using words like 'hello' and 'thank you'. I was operating under the idealized premise that every transaction starts and ends cleanly with these keywords. 

The make-or-break piece of this protocol is catching those exact keywords. In practice, the accuracy falls apart completely. customers don't always say formal greetings in a real noisy store! It's failing multiple times. It is working very average.

This path seemed extraordinarily promising because it logically mimics how human brains detect a new customer interaction in retail. 

Ultimately, the flaw in this logic is that it's failing because people are too unpredictable and overlapping. The real world doesn't follow strict greeting protocols. I checked with all three audio, and apart from one English file, both the Kannada audio were failing exponentially on keyword bounds.
