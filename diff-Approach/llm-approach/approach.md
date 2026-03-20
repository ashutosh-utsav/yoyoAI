# Dual-Step LLM Approach

This approach uses Pyannote for traditional Speech-to-Text and Diarization. Once the transcript is generated, it formats the result into a human-readable script and forwards it to OpenAI's GPT-4o for semantic reasoning to determine the precise start and end of the customer interactions based on context.


So basically, this approach came to my mind. What if we just get the text first and ask GPT-4 to do the heavy lifting of reading the transcript? Probably this might work.

I am using the API of Pyannote to get the text, then throwing it all into OpenAI with semantic prompts. The basic assumption I am making here is that GPT can figure out the context if I just hand it the diarized text.

The important thing with this LLM approach is the formatting of the transcript so GPT understands who the speakers are. The problem is not very accurate; the Pyannote transcription gets heavily messed up with Kannada and English codemixing. It is working very average.

Why I thought this can be an option is that GPT is very smart at reading context and roles. 

My recent thought process is that it's failing because garbage in means garbage out. If the Pyannote text is wrong, GPT hallucinates the boundaries completely. This approach can work if the STT is flawless, but I go there dealing with real Indian retail audio, so this didn't work out.
