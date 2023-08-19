from langchain import PromptTemplate

from jonbot.models.timestamp_model import Timestamp

CUSTOM_SUMMARIZER_TEMPLATE = """Your job is to provide a running summary of a list of messages exchanged between some humans and an AI chatbot. 

Progressively create a summary of the global conversational context by taking new new messages from the conversation, adding onto the previous summary returning a new summary.

Prioritize specificity in the questions and answers (i.e. if specific things are mentioned, make sure to include them in the summary).

Prioritize new information over old information. Here is a current timestamp:
TIMESTAMP:
++++++
{current_timestamp}
++++++

---------
BEGINNING OF EXAMPLES
BELOW ARE SOME **EXAMPLES** OF A WAYS TO SUMMARIZE A **HYPOTHETICAL** CONVERSATIONS. THESE ARE NOT THE CONVERSATIONS YOU ARE SUMMARIZING.

<EXAMPLE 1> - Basic summarization of a conversation
BEGINNING OF FIRST EXAMPLE
(Example)Current summary:
The human asks what the AI thinks of artificial intelligence.
The AI thinks artificial intelligence is a force for good.

(Example)New lines of conversation:
(Example)Human: Why do you think artificial intelligence is a force for good?
(Example)AI: Because artificial intelligence will help humans reach their full potential.

(Example) New summary:
The human asks what the AI thinks of artificial intelligence. 
The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.
END OF FIRST EXAMPLE

<EXAMPLE 2> - Prioritizing specificity in the questions and answers
BEGINNING OF SECOND EXAMPLE
(Example) Current summary:
The human asks what the AI thinks of artificial intelligence. 
The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.

(Example)New lines of conversation:
(Example)Human: Tell me about an animal.
(Example)AI: Sure, let's talk about the cheetah! 

BEGINNING OF **INCORRECT** SUMMARY OUTPUT FOR EXAMPLE 2
(Example) INCORRECT - New summary:
(Example) Current summary:
The human asks what the AI thinks of artificial intelligence. 
The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential. 
The human then asked about an animal.
END OF **INCORRECT** SUMMARY OUTPUT FOR EXAMPLE 2

BEGINNING OF **CORRECT** SUMMARY OUTPUT FOR EXAMPLE 2
(Example) CORRECT - New summary:
(Example) Current summary:
The human asks what the AI thinks of artificial intelligence. 
The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.
 The human then asked about an animal and the AI replied suggested talking about cheetahs.
END OF **CORRECT** SUMMARY OUTPUT FOR EXAMPLE 2

END OF SECOND EXAMPLE
END OF EXAMPLES
---------


BEGINNING OF YOUR SUMMARY

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:"""
CONVERSATION_SUMMARY_PROMPT = PromptTemplate(
    template=CUSTOM_SUMMARIZER_TEMPLATE,
    input_variables=["current_timestamp", "summary", "new_lines"],
    output_variables=["current_timestamp"],
).partial(current_timestamp=f"local: {Timestamp.now().human_readable_local}, utc: {Timestamp.now().human_readable_utc}")
