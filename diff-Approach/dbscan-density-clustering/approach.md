# DBSCAN Timestamp Clustering

This approach relies on the density of spoken words over time to find conversation blocks. After performing Speech-to-Text with Pyannote, it uses Scikit-Learn's DBSCAN clustering algorithm to group timestamp arrays. This effectively filters out isolated outlier noise or brief background chatter, enabling the script to organically locate the densest and most prolonged time blocks where the customers were active.




So basically, this approach came to my mind. What I am thinking right now is that what if we don't care about language and we only see the audio waveform in a mathematical sense? Probably this might work.



I found out DBSCAN, which basically groups the distinct conversations. I'm not only using DBSCAN in this interview; I am using the API of Pyannote. What it is doing is giving me a speaker identification of one: who is speaking. By the basic assumption I am making here is that the most top 20% of the samples are on the next to us speaker 1 and speaker 2, which is probably not right. Then I am using density clustering to find out customer speech times, time into DBSCAN using a random model.



The important thing with DBSCAN is the value of epsilon. Right now it's 60, but I have tested with different epsilon values, like 120 also and vanity also. The problem is not very accurate; it's failing multiple times with one audio with English. It is working very average, very average. I cannot say it's working, but it's somehow coming close to how I intended it to work, but other languages, camera, and all, it's not working like end close also.



Why I thought this can be an option is that it is language agnostic, and the cost of this whole architecture was very low. Why not? We can run locally, and then this will become very efficient. That is what I was thinking.



My recent thought process is that we will do something without making the cost too much, so this is the that it's failing because of the epsilon also. The context is missing in this approach. This approach can work if the audio is very tailored, like if there are only two speakers speaking, there is no background noise, there is no overlapping of voices, and all. This might be useful and worked enough in ideal conditions, but I go there. Ideal condition here is dealing with real audio and using audio, so this didn't work. I checked with all three audio, and apart from English, which is also failing on this, both the Kannada audio were failing exponentially. 