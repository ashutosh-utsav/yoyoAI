# Future Approaches & Brainstorming

*Use this document to organically brainstorm, outline, and log any new methodologies or architectures you think of for the audio boundary problem.*

---
# 1
So here are the ideas that are crossing my mind right now but I could not approach this. I think this might give a good result.

One of the ideas was to use a small language model. Probably a small language model will find that we have to fine-tune that model. What I'm thinking right now is that we take a small part of the audio, for example 10 seconds or 5 seconds, and send that to a sentiment analysis. We can use that to stitch that; that might work.

The problems that I can think of with this approach are that the content text of the whole conversation is something that we will be missing. I think that is why I'm thinking like this and why I've tried different kinds of approaches and why I'm not satisfied with my final Gemini approach. It is with regard to the costing so I wanted to make a system that can be done at a minimum cost and get the maximum output. That's what I'm thinking but of course I didn't have the time to do that so I am just writing down my thoughts.

What we can do is there is one like this I can think of. 




# 2

So another idea that I am getting is if somehow we clean the audio pretty well. What I found with all the approaches I have tried and with all the research I have done in this time frame is that the main problem, the main culprit, was the audio. I looked at lots of tools to see if I can remove the background noises but the main problem I was getting is that the audio is overlapping each other. The conversations are overlapping so we are not in an ideal situation.

I also am interested and now I'll dig deep into the territory of how we can treat this audio in a way that can get the maximum output of what we want from this audio. I could not get a deep dive into how the whole audio is working under the hood but I will be doing this because this is something that I'm interested in. That is another thing: if we get the audio very clean somehow, I've made the audio somehow better than this, then I can simply use a transcription and then I use a basic LM call. That will be a very robust system. If I found that in regards to costing it's not very cheap but it will be very very very robust.

Yeah that is one thing that is going on: how to trick that audio data so that I'll do probably.



# 3

So another thing that I wanted to try with this is to explore Hugging Face to see different kinds of open source models. I did try to run AI for Bharat models for transcription, which didn't work very well because I have a Mac and there was an issue there. I could not dive into it because of the time but I'd like to try lots of open source models, lots of libraries that I saw, like ng-rox, which can enhance audio and give me probably a better transcription. Another thing, so that is the one place that I want to explore more about how this can be done. This is the third approach of trying lots of open source things, lots of open source libraries, lots of open source models. This is something that I would look upon after this.