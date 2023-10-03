import asyncio
import json
from pathlib import Path
from typing import Dict, List

from langchain import ConversationChain, PromptTemplate
from langchain.callbacks import StdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationEntityMemory

from jonbot.backend.data_layer.analysis.get_server_chats import get_server_chats
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.backend.data_layer.models.discord_stuff.discord_message_document import DiscordMessageDocument

_DEFAULT_TOPIC_CONVERSATION_TEMPLATE = """

Your job is to examine a conversation between a student and an AI chatbot and extract the topics (entities) that they discussed. 

Context:
{entities}

Current conversation:
{history}
Last line:
Human: {input}
You:"""

TOPIC_CONVERSATION_TEMPLATE = PromptTemplate(
    input_variables=["entities", "history", "input"],
    template=_DEFAULT_TOPIC_CONVERSATION_TEMPLATE,
)

_DEFAULT_TOPIC_SUMMARIZATION_TEMPLATE = """You are an AI assistant helping a human keep track of topics (entities) that a student has been disussing with a chatbot. Update the summary of the provided topics (entities) in the "Topics" section based on the last line of your conversation with the human. If you are writing the summary for the first time, return a single sentence.
The update should only include facts that are relayed in the last line of conversation about the provided topic, and should only contain facts about the provided entity.

If there is no new information about the provided topic or the information is not worth noting (not an important or relevant fact to remember long-term), return the existing summary unchanged.

Full conversation history (for context):
{history}

Topics to summarize:
{entity}

Existing summary of {entity}:
{summary}

Last line of conversation:
Human: {input}
Updated summary:"""

TOPIC_SUMMARIZATION_PROMPT = PromptTemplate(
    input_variables=["entity", "summary", "history", "input"],
    template=_DEFAULT_TOPIC_SUMMARIZATION_TEMPLATE,
)

_DEFAULT_TOPIC_EXTRACTION_TEMPLATE = """You are an AI assistant reading the transcript of a conversation between an AI and a human. Extract all of the topics  from the last line of conversation that are relevant to this course;

```
## Course Description
Students will explore the neural basis of natural human behavior in real-world contexts (e.g., [sports], [dance], or [everyday-activities]) by investigating the [neural-control] of [full-body] [human-movement]. The course will cover [philosophical], [technological], and [scientific] aspects related to the study of [natural-behavior] while emphasizing hands-on, project-based learning. Students will use [free-open-source-software], and [artificial-intelligence],[machine-learning] and [computer-vision] driven tools and methods to record human movement in unconstrained environments.

The course promotes interdisciplinary collaboration and introduces modern techniques for decentralized [project-management], [AI-assisted-research-techniques], and [Python]-based programming (No prior programming experience is required). Students will receive training in the use of AI technology for project management and research conduct, including [literature-review], [data-analysis], [data-visualization], and [presentation-of-results]. Through experiential learning, students will develop valuable skills in planning and executing technology-driven research projects while examining the impact of structural inequities on scientific inquiry.

    
## Course Objectives
- Gain exposure to key concepts related to neural control of human movement.
- Apply interdisciplinary approaches when collaborating on complex problems.
- Develop a basic understanding of machine-learning tools for recording human movements.
- Contribute effectively within a team setting towards achieving common goals.
- Acquire valuable skills in data analysis or background research.
```

Return the output as a single comma-separated list, or NONE if there is nothing of note to return (e.g. the user is just issuing a greeting or having a simple conversation).

EXAMPLE
Conversation history:
Person #1: how's it going today?
AI: "It's going great! How about you?"
Person #1: good! I'm curiuos about the cerebellum. What does it do?
AI: "The cerebellum is a part of the brain that controls movement and balance. It also helps with coordination, posture, and speech."
Last line:
Person #1: "Good! I'm curiuos about the cerebellum. What does it do?"
Output: Cerebellum, Neuroscience, Brain
END OF EXAMPLE

EXAMPLE
Conversation history:
Person #1: how's it going today?
AI: "It's going great! How about you?"
Person #1: good! I'm curiuos about the cerebellum. What does it do?
AI: "The cerebellum is a part of the brain that controls movement and balance. It also helps with coordination, posture, and speech."
Person #1: "That's interesting! How an we use motion capture to study the cerebellum?"
AI: "Motion capture is a technology that records the movement of objects or people. It can be used to study the cerebellum by recording how it affects a person's movements.
Last line:
Person #1: "That's interesting! How an we use motion capture to study the cerebellum?"
Output: Motion capture, Neuroscience, Brain, Technology
END OF EXAMPLE

Conversation history (for reference only):
{history}
Last line of conversation (for extraction):
Human: {input}

Output:"""
TOPIC_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["history", "input"], template=_DEFAULT_TOPIC_EXTRACTION_TEMPLATE
)


def calculate_entity_memory(chats: Dict[str, DiscordChatDocument]):
    llm = ChatOpenAI(temperature=0,
                     model_name="gpt-3.5-turbo",
                     callbacks=[StdOutCallbackHandler()],
                     streaming=True)

    entity_memory = ConversationEntityMemory(llm=llm,
                                             entity_extraction_prompt=TOPIC_EXTRACTION_PROMPT,
                                             entity_summarization_prompt=TOPIC_SUMMARIZATION_PROMPT,
                                             )
    conversation_chain = ConversationChain(
        llm=llm,
        verbose=True,
        prompt=TOPIC_CONVERSATION_TEMPLATE,
        memory=entity_memory
    )
    chat_entity_stores = {}
    for chat_id, chat in chats.items():
        for message in chat.messages:
            conversation_chain.run(input=message.content)
        json_path = Path("entity_memory.json")
        chat_entity_stores[chat_id] = entity_memory.entity_store.store
        with json_path.open('w', encoding="utf-8") as file:
            json.dump(chat_entity_stores, file, indent=4)
    return entity_memory


if __name__ == "__main__":
    database_name = "classbot_database"
    server_id = 1150736235430686720
    chats_in = asyncio.run(get_server_chats(database_name=database_name,
                                         server_id=server_id))
    entity_memory = calculate_entity_memory(chats=chats_in)



