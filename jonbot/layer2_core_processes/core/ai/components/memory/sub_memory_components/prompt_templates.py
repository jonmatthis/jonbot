from langchain import PromptTemplate

CUSTOM_SUMMARIZER_TEMPLATE = """Progressively summarize the lines of conversation provided, adding onto the previous summary returning a new summary.

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
CUSTOM_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["summary", "new_lines"], template=CUSTOM_SUMMARIZER_TEMPLATE
)
