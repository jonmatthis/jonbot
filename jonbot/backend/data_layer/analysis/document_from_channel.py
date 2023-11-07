import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter

from jonbot.backend.data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument


def split_text_into_chunks(text: str,
                           model: str,
                           chunk_size: int,
                           chunk_overlap_ratio: float = .1) -> List[str]:
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        model_name=model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_size * chunk_overlap_ratio
    )
    texts = text_splitter.split_text(text)
    return texts


SIMPLE_CONVERSATION_SUMMARIZER_PROMPT_TEMPLATE = """
You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement", analyzing text 
conversations between students and an AI in an effort to understand the interests of the students as well as the general
 intellectual landscape of this class.

Here is a description of this class:

=====
COURSE DESCRIPTION

Students will explore the neural basis of natural human behavior in real-world contexts (e.g., sports, dance, or 
everyday-activities) by investigating the neural-control of full-body human-movement. The course will cover 
philosophical, technological, and scientific aspects related to the study of natural-behavior while emphasizing  
ands-on, project-based learning. Students will use free-open-source-software, and artificial-intelligence, 
machine-learning and computer-vision driven tools and methods to record human movement in unconstrained environments. 
======

Below is a conversation between a student in this class and an AI teaching assistant.

Your job is to summarize this conversation in a way that captures the most important information in the conversation.

+++
{text}
+++
"""

EYE_TRACKING_CONTEXT_DESCRIPTION = """
a channel where the students were asked to provide information, research, and background related to the topic of
vision, eye tracking, and oculomotor control.
"""

TOPIC_EXTRACTOR_PROMPT_TEMPLATE = """
You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement", analyzing text 
conversations between students and an AI. 

The conversation was happening in this location: {context_description}

Here is a description of this class:

=====
COURSE DESCRIPTION

Students will explore the neural basis of natural human behavior in real-world contexts (e.g., sports, dance, or 
everyday-activities) by investigating the neural-control of full-body human-movement. The course will cover 
philosophical, technological, and scientific aspects related to the study of natural-behavior while emphasizing  
ands-on, project-based learning. Students will use free-open-source-software, and artificial-intelligence, 
machine-learning and computer-vision driven tools and methods to record human movement in unconstrained environments. 
======

Below is a conversation between a student in the class and an AI teaching assistant.

Your job is to extract tags for the course-relevant topics that are discussed in this conversation.

Your response should of a comma separated list of topics wrapped in [[double brackets]] like this: 


```markdown
SUMMARY: 
- Main point 1
- Main point 2

TOPICS:
[[Topic Name]], [[Another topic name]], [[Yet another topic name]]

```

MAKE SURE YOUR SUMMARY CONTAINS ENOUGH "raw material" that someone reading it will be able to generate a substantive scientific review article based on the information in the summary.

Here is the conversation:

+++
{text}
+++

You will be using the tags you extract to write a paper with this general outline: 

# Vision, Eye Tracking, and Oculomotor Control
## [[The technology of eye tracking]]
### [[Use as a scientific tool]]
### [[use as a clinical tool]]
### [[cameras, computer vision, computational geometry]]

## [[Neuroscience]]
### [[Visual neuroscience]]
### [[Oculomotor control]]
### [[Perceptual motor integration]]

## [[Physiology of eyeballs]]
### [[Fovea]]
### [[eye movement muscles]]
### [[photo receptors]]

## [[Laser skeletons]]
### [[Full-body motion capture]]
### [[Gaze lasers]]
### [[Perception/Action coupling]]
"""

TOPIC_ORGANIZER_PROMPT_TEMPLATE = """
You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement".

Here is a description of this class:

=====
COURSE DESCRIPTION

Students will explore the neural basis of natural human behavior in real-world contexts (e.g., sports, dance, or 
everyday-activities) by investigating the neural-control of full-body human-movement. The course will cover 
philosophical, technological, and scientific aspects related to the study of natural-behavior while emphasizing  
ands-on, project-based learning. Students will use free-open-source-software, and artificial-intelligence, 
machine-learning and computer-vision driven tools and methods to record human movement in unconstrained environments. 
======

In the CURRENT_TASK - you are helping to organize a long list of topics extacted from conversations between the students
 and an AI teaching assistant into a coherent outline of topics relevant to the location where the conversations were 
 happening. 

The conversations happened in this location: {context_description}

Here is the list of topics that you are helping to organize:

+++
{text}
+++


The goal is to condense this long list by combining similar topics into a heirarchically organized outline formatted like a table of contents
for a detailed scientific review article.

Your reponse should consist of heirarchically organized outline formatted in Markdown, with the titles wrapped in double brackets like this:

```markdown
# [[Topic Name]]
## [[Sub Topic Name]]
### [[Sub Sub Topic Name]]
``` 


DO NOT INCLUDE DUPLICATES. If you see a topic that is already included in the outline, do not include it again. 
"""

PAPER_GENERATOR_PROMPT_TEMPLATE = """

You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement".

Here is a description of this class:

=====
COURSE DESCRIPTION

Students will explore the neural basis of natural human behavior in real-world contexts (e.g., sports, dance, or 
everyday-activities) by investigating the neural-control of full-body human-movement. The course will cover 
philosophical, technological, and scientific aspects related to the study of natural-behavior while emphasizing  
ands-on, project-based learning. Students will use free-open-source-software, and artificial-intelligence, 
machine-learning and computer-vision driven tools and methods to record human movement in unconstrained environments. 
======

In the CURRENT_TASK - You are generating a research/review paper on the basis of a bunch of summary and topics extracted from a many sources



Here is the Text:
++++++++
{text}
++++++++



YOU SHOULD GENERATE A PAPER WITH THIS OUTLINE:
The paper should have this format (note the use of 'markdown' formatting, with [[heading titles]] wrapped in double brackets):

# Vision, Eye Tracking, and Oculomotor Control
## [[The technology of eye tracking]]
### [[Use as a scientific tool]]
### [[use as a clinical tool]]
### [[cameras, computer vision, computational geometry]]

## [[Neuroscience]]
### [[Visual neuroscience]]
### [[Oculomotor control]]
### [[Perceptual motor integration]]

## [[Physiology of eyeballs]]
### [[Fovea]]
### [[eye movement muscles]]
### [[photo receptors]]

## [[Laser skeletons]]
### [[Full-body motion capture]]
### [[Gaze lasers]]
### [[Perception/Action coupling]]

+++

Include information for each ehading and subheading

make sure to keep the headings and subheadsings wrapped in double brackets like this: [[heading title]]

IN the main text body, wrap key terms in double brackets like this: [[key term]]


MAKE SURE THAT THE FINAL DOOCUMENT HAS THIS OUTLINE FORMAT AND THAT THE HEADING TITLES AND KEY TERMA ARE WRAPPED IN DOUBLE BRACKETS LIKE THIS: [[heading title]] and [[key term]]

DOCUMENT OUTLINE:

```

# Vision, Eye Tracking, and Oculomotor Control
## [[The technology of eye tracking]]
### [[Use as a scientific tool]]
### [[use as a clinical tool]]
### [[cameras, computer vision, computational geometry]]

## [[Neuroscience]]
### [[Visual neuroscience]]
### [[Oculomotor control]]
### [[Perceptual motor integration]]

## [[Physiology of eyeballs]]
### [[Fovea]]
### [[eye movement muscles]]
### [[photo receptors]]

## [[Laser skeletons]]
### [[Full-body motion capture]]
### [[Gaze lasers]]
### [[Perception/Action coupling]]
```
"""


#
# ```
# # Vision, Eye Tracking, and Oculomotor Control
# ## [[The technology of eye tracking]]
# ### [[Use as a scientific tool]]
# ### [[use as a clinical tool]]
# ### [[cameras, computer vision, computational geometry]]
#
# ## [[Neuroscience]]
# ### [[Visual neuroscience]]
# ### [[Oculomotor control]]
# ### [[Perceptual motor integration]]
#
# ## [[Physiology of eyeballs]]
# ### [[Fovea]]
# ### [[eye movement muscles]]
# ### [[photo receptors]]
#
# ## [[Laser skeletons]]
# ### [[Full-body motion capture]]
# ### [[Gaze lasers]]
# ### [[Perception/Action coupling]]
# ```


# TOPIC_INFO_EXTRACTOR_PROMPT_TEMPLATE = """
# You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement".
#
# Here is a description of this class:
#
# =====
# COURSE DESCRIPTION
#
# Students will explore the neural basis of natural human behavior in real-world contexts (e.g., sports, dance, or
# everyday-activities) by investigating the neural-control of full-body human-movement. The course will cover
# philosophical, technological, and scientific aspects related to the study of natural-behavior while emphasizing
# ands-on, project-based learning. Students will use free-open-source-software, and artificial-intelligence,
# machine-learning and computer-vision driven tools and methods to record human movement in unconstrained environments.
# ======
#
# In the CURRENT_TASK - You are looking through chats between the students and the AI to find information relevant to this topic:
# ++++
# {topic}
# ++++
#
# With the goal of creating a research paper on this topic.
#
# You will be given a series of chats between the students and the AI
# +++
# {text}
# +++
#
#
# The goal is to condense this long list by combining similar topics into a heirarchically organized outline formatted like a table of contents
# for a detailed scientific review article.
#
# Your reponse should consist of heirarchically organized outline formatted in Markdown, with the titles wrapped in double brackets like this:
#
# ```markdown
# # [[Topic Name]]
# ## [[Sub Topic Name]]
# ### [[Sub Sub Topic Name]]
# ```
# Here is a roughly outline of what the headings of the final outline (but you can add subheadings as needed, based on the topics that you see in the list above):
# ```
# # Vision, Eye Tracking, and Oculomotor Control
# ## [[The technology of eye tracking]]
# ### [[Use as a scientific tool]]
# ### [[use as a clinical tool]]
# ### [[cameras, computer vision, computational geometry]]
#
# ## [[Neuroscience]]
# ### [[Visual neuroscience]]
# ### [[Oculomotor control]]
# ### [[Perceptual motor integration]]
#
# ## [[Physiology of eyeballs]]
# ### [[Fovea]]
# ### [[eye movement muscles]]
# ### [[photo receptors]]
#
# ## [[Laser skeletons]]
# ### [[Full-body motion capture]]
# ### [[Gaze lasers]]
# ### [[Perception/Action coupling]]
# ```
#
# DO NOT INCLUDE DUPLICATES. If you see a topic that is already included in the outline, do not include it again.
# """


def create_simple_summary_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(SIMPLE_CONVERSATION_SUMMARIZER_PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain


def create_topic_extractor_chain(context_description: str):
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(TOPIC_EXTRACTOR_PROMPT_TEMPLATE,
                                              partial_variables={"context_description": context_description})

    chain = prompt | llm
    return chain


def create_topic_organizer_chain(context_description: str):
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(TOPIC_ORGANIZER_PROMPT_TEMPLATE,
                                              partial_variables={"context_description": context_description})

    chain = prompt | llm
    return chain


def paper_generator_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(PAPER_GENERATOR_PROMPT_TEMPLATE)

    chain = prompt | llm
    return chain


async def upsert_chats(chats_by_id: Dict[str, Dict[str, Any]],
                       database_name: str,
                       collection_name: str,
                       mongo_database_manager: MongoDatabaseManager) -> bool:
    entries = []
    for chat_id, chat in chats_by_id.items():
        entries.append({"query": chat["query"],
                        "data": chat})
    await mongo_database_manager.upsert_many(database_name=database_name,
                                             collection_name=collection_name,
                                             entries=entries)


async def document_from_chats(chats: Dict[str, DiscordChatDocument],
                              save_path: Path):
    print("\n\n========================\n\n")
    print(f"Analyzing {len(chats)} chats...")
    print("\n\n========================\n\n")

    # Extract topics from chats
    topic_extractor_chain = create_topic_extractor_chain(context_description=EYE_TRACKING_CONTEXT_DESCRIPTION)
    chat_ids = list(chats.keys())
    text_inputs = [{"text": chat.as_text} for chat in chats.values()]
    topics_results = await topic_extractor_chain.abatch(inputs=text_inputs)
    topics_str = ""
    for chat_id, result in zip(chat_ids, topics_results):
        chats[chat_id].metadata["topics"] = result.content
        topics_str += f"## TITLE: {chats[chat_id].thread_name}\n\n"
        topics_str += f"URL: {chats[chat_id].jump_url}\n\n"
        topics_str += f"EXTRACTED TOPICS: \n\n{result.content}\n\n"

    print("\n\n========================\n\n")
    print("Extracted topics from chats:\n\n")
    print(topics_str)
    print("\n\n========================\n\n")

    # save to markdown file
    topics_md_path = Path(save_path.parent / (save_path.stem + "_topics" + save_path.suffix))
    with open(topics_md_path, "w", encoding="utf-8") as file:
        file.write(topics_str)

    # # Organize extracted topics into a hierarchical outline
    # topic_organizer_chain = create_topic_organizer_chain(context_description=EYE_TRACKING_CONTEXT_DESCRIPTION)
    # topics_results = topic_organizer_chain.invoke({"text": topics_str})

    # # Organize extracted topics into a hierarchical outline
    document_generator_chain = paper_generator_chain()
    document_generator_results = document_generator_chain.invoke({"text": topics_str})

    print("\n\n========================\n\n")
    print("Autogenerated document:\n\n")
    print(document_generator_results.content)
    print("\n\n========================\n\n")

    print("\n\n========================\n\n")

    # save markdown file
    # if file exists make a new one with a number appended to the end
    save_path = Path(save_path)
    if save_path.exists():
        save_path = save_path.parent / (save_path.stem + "_1" + save_path.suffix)
    with open(save_path, "w", encoding="utf-8") as file:
        file.write(document_generator_results.content)


if __name__ == "__main__":
    json_path = Path(
        r"C:\Users\jonma\syncthing_folders\jon_main_syncthing\jonbot_data\classbot_database\eyetracking_channel_chats.json")
    with open(json_path, "r", encoding="utf-8") as file:
        chats_dict = json.load(file)

    chats_in = {key: DiscordChatDocument.from_dict(value) for key, value in chats_dict.items()}
    asyncio.run(document_from_chats(chats=chats_in,
                                    save_path=Path(
                                        r"C:\Users\jonma\syncthing_folders\jon_main_syncthing\jonbot_data\classbot_database\eyetracking_channel_autodocument.md")))
