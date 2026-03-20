# Dual-Step LLM Approach

This approach uses Pyannote for traditional Speech-to-Text and Diarization. Once the transcript is generated, it formats the result into a human-readable script and forwards it to OpenAI's GPT-4o for semantic reasoning to determine the precise start and end of the customer interactions based on context.


Another route I sketched out was purely text-driven. I figured, what if we just get the text first and ask GPT-4 to do the heavy lifting of reading the transcript? Probably this might work.

I am using the API of Pyannote to get the text, then throwing it all into OpenAI with semantic prompts. The whole architecture rested on the assumption that GPT can figure out the context if I just hand it the diarized text.

The absolute bottleneck with this LLM approach is the formatting of the transcript so GPT understands who the speakers are. The reality is radically different; the outputs are scattered. the Pyannote transcription gets heavily messed up with Kannada and English codemixing. It is working very average.

I banked on this methodology initially because GPT is very smart at reading context and roles. 

What I eventually concluded from the trial runs is that it's failing because garbage in means garbage out. If the Pyannote text is wrong, GPT hallucinates the boundaries completely. This approach can work if the STT is flawless, but I go there dealing with real Indian retail audio, so this didn't work out.
