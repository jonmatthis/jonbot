from langchain import PromptTemplate

from jonbot.models.timestamp_model import Timestamp

CUSTOM_SUMMARIZER_TEMPLATE = """Your job is to provide a running summary of a list of messages exchanged between some humans and an AI chatbot. 

Progressively create a summary of the global conversational context by taking new new messages from the conversation, adding onto the previous summary returning a new summary.

Prioritize new information over old information. Here is a current timestamp:
TIMESTAMP:
++++++
{current_timestamp}
++++++

---------
THIS IS AN **EXAMPLE** OF A WAY TO SUMMARIZE A **DIFFERENT** CONVERSATION. THIS IS NOT THE CONVERSATION YOU ARE SUMMARIZING.
EXAMPLE
Current summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good.

New lines of conversation:
(Example)Human: Why do you think artificial intelligence is a force for good?
(Example)AI: Because artificial intelligence will help humans reach their full potential.

New summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.
END OF EXAMPLE

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
