from langchain import PromptTemplate

from jonbot.backend.data_layer.models.timestamp_model import Timestamp

CUSTOM_SUMMARIZER_TEMPLATE = """Your job is to provide a running summary of a list of messages exchanged between some humans and an AI chatbot. 

Progressively create a summary of the global conversational context by taking new new messages from the conversation, adding onto the previous summary returning a new summary.




Messages may have [metadata] included, which includes helpful information such as the username of the human or ai chatbot that is speaking or the timestamp when the message was sent (in the Human's local time), with the schema:
[metadata - 'username':(chat_message.speaker.name),'local_time': (chat_message.timestamp.human_readable_local)]

The [metadata] information WAS NOT SENT by the human or ai chatbot, it is just there to help you contextualize the conversation (e.g. noticing when different humans or AI chatbots are speaking, or noticing when there is a long delay, etc).
Metadata is not important to include in the summary, but may be is helpful to contextualize the conversation.

Prioritize new information over old information. Here is a current timestamp:
TIMESTAMP:
++++++
{current_timestamp}
++++++

---------
BEGINNING OF EXAMPLES
BELOW ARE SOME **EXAMPLES** OF A WAYS TO SUMMARIZE A **HYPOTHETICAL** CONVERSATIONS. THESE ARE NOT THE CONVERSATIONS YOU ARE SUMMARIZING.


<EXAMPLE 0> - Basic summarization of a conversation
BEGINNING OF <EXAMPLE 0>
(Example)CURRENT SUMMARY:
The human asks what the AI thinks of artificial intelligence. 
The AI thinks artificial intelligence is a force for good.

(Example)NEW LINES OF CONVERSATION:
(Example)Human: Why do you think artificial intelligence is a force for good? [metadata - 'username':Human,'local_time': 2021-08-04 12:00:00]
(Example)AI: Because artificial intelligence will help humans reach their full potential. [metadata - 'username':AI,'local_time': 2021-08-04 12:00:01]

(Example) NEW SUMMARY:
The human asks what the AI thinks of artificial intelligence. 
The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.

END OF <EXAMPLE 0>


<EXAMPLE 1> - Prioritize specificity in the questions and answers (i.e. if specific things are mentioned, make sure to include them) in the summary).
BEGINNING OF <EXAMPLE 1>
(Example) CURRENT SUMMARY:
2021-08-04 12:00:00: the human (jonmatthis) asked what the AI thinks of artificial intelligence.
The AI (JonBot) replied that it thinks that artificial intelligence is a "force for good" because it will help humans reach their full potential.

(Example)NEW LINES OF CONVERSATION:
(Example)Human: Tell me about an animal. [metadata - 'username':alice,'local_time': 2021-08-04 18:00:02]
(Example)AI: Sure, let's talk about the cheetah! They are the fastest land animal. [metadata - 'username':AI,'local_time': 2021-08-04 18:00:03]

(Example) NEW SUMMARY:
A few hours ago, the human (jonmatthis) and the AI (JonBot) talked about AI, the AI said it was a "force for good"
At around 2021-08-04 18:00:02, the human (alice) asked the AI (JonBot) to "tell me about an animal" and the AI (JonBot) talked about cheetahs.

END OF <EXAMPLE 1>

<EXAMPLE 2> - Prioritize the recent information over the older information, and include more information about the recent information.
BEGINNING OF <EXAMPLE 2>
(Example) CURRENT SUMMARY:
A few hours ago, the human (jonmatthis) and the AI (JonBot) talked about AI, the AI said it was a "force for good"
At around 2021-08-04 18:00:02, the human (alice) asked the AI (JonBot) to "tell me about an animal" and the AI (JonBot) talked about cheetahs.


(Example)NEW LINES OF CONVERSATION:
(Example)Human: Cheetahs are cool! 😻 [metadata - 'username':jon,'local_time': 2021-08-05 18:00:04]
(Example)AI: I agree! I also like penguins 🐧 [metadata - 'username':AI,'local_time': 2021-08-05 18:00:05]

(Example) NEW SUMMARY:
A while ago, the human (jonmatthis) and the AI (JonBot) talked about AI, the AI said it was a "force for good"
More recently, the human (alice) asked the AI (JonBot) to "tell me about an animal" and the AI (JonBot) talked about cheetahs.
A day later, the human (jon) said "Cheetahs are cool! 😻" and the AI (JonBot) agreed and mentioned penguins.

END OF <EXAMPLE 2>

END OF EXAMPLES
---------


BEGINNING OF YOUR SUMMARY

CURRENT SUMMARY:

{summary}

NEW LINES OF CONVERSATION:

{new_lines}

NEW SUMMARY:"""

CONVERSATION_SUMMARY_PROMPT = PromptTemplate(
    template=CUSTOM_SUMMARIZER_TEMPLATE,
    input_variables=["current_timestamp", "summary", "new_lines"],
    output_variables=["current_timestamp"],
).partial(
    current_timestamp=f"local: {Timestamp.now().human_friendly_local}, utc: {Timestamp.now().human_friendly_utc}"
)
