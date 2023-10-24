import asyncio
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Hashable

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from magic_tree.magic_tree_dictionary import MagicTreeDictionary

from jonbot.backend.data_layer.analysis.get_chats import get_chats
from jonbot.backend.data_layer.database.get_mongo_database_manager import get_mongo_database_manager
from jonbot.backend.data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.system.environment_variables import CLASSBOT_SERVER_ID
from jonbot.system.path_getters import get_default_backup_save_path


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
Summarize this conversation:

+++
{text}
+++
"""

TOPIC_EXTRACTOR_PROMPT_TEMPLATE = """
You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement", analyzing text 
conversations between students and an AI in an effort to understand the interests of the students as well as the general
 intellectual landscape of this class.

Below is a summary of a conversation between a student in a class called "The Neural Control of Real World Human Movement" 
and an AI teaching assistant.

Your job is to extract topic tags from this conversation that can be used to categorize the relationship between this 
conversation and the broader context of the class.

Remember - Your job is to extract topic tags from this conversation that can be used to categorize the relationship 
between this conversation and the broader context of the class.

Your topic tags should be formatted as individual tags in kebab-case-lowercase preceeded by a #hash-tag separated by commas, 
like this: '#tag-name,  #tag-name-2, #tag-name-3'

If the topic is not relevant to this course, simply tag it as `#off-topic`

EXAMPLE:

++++
BEGIN-EXAMPLE
EXAMPLE_SUMMARY:
"The Human asked the AI about the use of motion capture in the study of human movement and the AI explained how motion
    capture is used to record human movement in real-world contexts. The student asked whether it could be used to study people with cerebellar disorders
    and the AI provded details about how motion capture could be use din clinical settings" 
    
TOPICS:
#neuoscience, #technology, #motion-capture, #cerebellum, #movement-disorders, #clinical-settings
END-EXAMPLE
++++


Here is a description of this class:

=====
COURSE DESCRIPTION

Students will explore the neural basis of natural human behavior in real-world contexts (e.g., sports, dance, or 
everyday-activities) by investigating the neural-control of full-body human-movement. The course will cover 
philosophical, technological, and scientific aspects related to the study of natural-behavior while emphasizing  
ands-on, project-based learning. Students will use free-open-source-software, and artificial-intelligence, 
machine-learning and computer-vision driven tools and methods to record human movement in unconstrained environments. 
======


Here is a summary of the conversation:

+++
{text}
+++
"""


def create_topic_extractor_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(TOPIC_EXTRACTOR_PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain


def nested_dict_to_markdown(tree_dict: Dict[str, Any],
                            markdown_string: str = "",
                            depth: int = 0) -> str:
    for key, value in tree_dict.items():
        if isinstance(value, dict) and key != "chat":
            if "chat" in value.keys():
                markdown_string += f"{'#' * (depth + 1)} **CHAT TITLE:**\n\n`{key}`\n\n"
            else:
                markdown_string += f"{'#' * (depth + 1)} {key}\n\n"
            markdown_string = nested_dict_to_markdown(tree_dict=value,
                                                      markdown_string=markdown_string,
                                                      depth=depth + 1)
        else:
            markdown_string += f"**Speakers:**\n\n {value['speakers']}\n\n"
            if "summary" in value.keys():
                markdown_string += f"**Summary:**\n\n```\n{value['summary']}\n```\n\n"
            markdown_string += f"**Text:** \n\n```\n{value['text']}\n```\n\n___\n\n"

    return markdown_string


def save_chat_tree_to_markdown_directory(tree: MagicTreeDictionary,
                                         directory_root: str):
    chat_tree_paths = tree.get_paths_to_keys(keys=["chat_text"])
    root_path = Path(directory_root)
    for chat_tree_path in chat_tree_paths:
        chat_folder_path = root_path
        for thing in list(chat_tree_path[:-1]):
            thing = thing.replace(" ", "_").replace(":", "_")
            chat_folder_path = chat_folder_path / thing
        chat_folder_path.parent.mkdir(parents=True, exist_ok=True)
        file_name = chat_tree_path[-2].replace(" ", "_").replace(":", "_") + ".md"
        chat_save_path = chat_folder_path.parent / file_name

        chat_file_text = ""
        chat_file_text += f"# Title: {chat_folder_path.stem}\n\n"
        speaker_string = ""
        for speaker in tree[chat_tree_path[:-1]]["speakers"]:
            for key, value in speaker.items():
                speaker_string += f"{key}: {value}\n\n"
        chat_file_text += f"## Speakers: \n\n{speaker_string}\n\n"
        chat_file_text += f"Jump URL: \n\n{tree[chat_tree_path[:-1]]['jump_url']}\n\n"
        chat_file_text += f"Context Description: \n\n{tree[chat_tree_path[:-1]]['context_description']}\n\n"
        chat_file_text += f"## Summary: \n\n{tree[chat_tree_path[:-1]]['simple_summary']}\n\n"
        chat_file_text += f"## Topics: \n\n{tree[chat_tree_path[:-1]]['topics']}\n\n"
        chat_file_text += f"## Text: \n\n```\n{tree[chat_tree_path[:-1]]['chat_text']}\n```\n\n"

        chat_save_path.write_text(chat_file_text, encoding="utf-8")


def create_simple_summary_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(SIMPLE_CONVERSATION_SUMMARIZER_PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain


async def analyze_leaves(tree: MagicTreeDictionary, leaf_key: Hashable, chains: Dict[str, Any]) -> MagicTreeDictionary:
    try:
        leaf_paths = tree.get_paths_to_keys(keys=[leaf_key])

        for chain_name, chain in chains.items():
            if isinstance(chain, dict):
                parser = chain["parser"]
                chain = chain["chain"]
            else:
                parser = None

            text_inputs = [{"text": tree[path]} for path in leaf_paths]
            results = await chain.abatch(inputs=text_inputs)
            for path, result in zip(leaf_paths, results):
                if parser:
                    content = result.content
                    content.replace("TOPICS:\n", "").replace(",", ",\n")
                #     parsed_result = parser.invoke(result)
                tree[path[:-1]][chain_name] = result.content
    except Exception as e:
        print(f"Failed to analyze leaves: {e}")
        raise e
    return tree


async def upsert_tree(tree: MagicTreeDictionary,
                      database_name: str,
                      collection_name: str,
                      query: dict,
                      mongo_database_manager: MongoDatabaseManager) -> bool:
    return await mongo_database_manager.upsert_one(database_name=database_name,
                                                   collection_name=collection_name,
                                                   data=tree.to_dict(),
                                                   query=query)


def chats_to_magic_tree(chats_by_id):
    tree = MagicTreeDictionary()
    for chat_id, chat in chats_by_id.items():
        if not isinstance(chat, DiscordChatDocument):
            chat = DiscordChatDocument(**chat.dict())
        chat_path = chat.context_route.as_friendly_tree_path
        tree[chat_path]["chat_text"] = chat.as_text

        tree[chat_path]["speakers"] = [speaker.dict() for speaker in chat.speakers]

        tree[chat_path]["owner"] = {"name": chat.owner_name,
                                    "id": chat.owner_id}
        tree[chat_path]["jump_url"] = chat.jump_url
        tree[chat_path]["context_description"] = chat.context_description
        tree[chat_path]["context_route"] = chat.context_route.dict()
        tree[chat_path]["created_at"] = chat.created_at.dict()
        tree[chat_path]["last_accessed"] = chat.last_accessed.dict()
        for couplet_number, couplet in enumerate(chat.couplets):
            tree[chat_path]["couplets"][str(couplet_number)]["couplet_text"] = couplet.text
    return tree


async def run_summary_analysis():
    mongo_database_manager = await get_mongo_database_manager()

    try:
        database_name_in = "classbot_database"
        server_id = CLASSBOT_SERVER_ID
        chats_by_id = await get_chats(mongo_database_manager=mongo_database_manager,
                                      database_name=database_name_in,
                                      query={"server_id": server_id})

        chats_by_id_json_path = Path(get_default_backup_save_path(filename="classbot_chats_by_chat_id",
                                                                  subfolder=database_name_in))
        if not chats_by_id_json_path.exists():
            chats_by_id_json_path.write_text(
                json.dumps({chat_id: chat.dict() for chat_id, chat, in chats_by_id.items()}, indent=4),
                encoding="utf-8")

        chat_tree = chats_to_magic_tree(chats_by_id)
        simple_summary_chain = {"simple_summary": create_simple_summary_chain()}

        chat_tree = await analyze_leaves(tree=chat_tree,
                                         leaf_key="chat_text",
                                         chains=simple_summary_chain)
        topics_chain = {"topics": create_topic_extractor_chain()}
        # "parser": PydanticOutputParser(pydantic_object=TopicTags)}
        chat_tree = await analyze_leaves(tree=chat_tree,
                                         leaf_key="simple_summary",
                                         chains=topics_chain)

        # chat_tree_with_summaries_and_tags = await analyze_leaves(tree=chat_tree_with_chat_summaries,
        #                                                          leaf_key="simple_summary",
        #                                                          chains={"topics": create_topic_extractor_chain()})

        success = await upsert_tree(tree=chat_tree,
                                    database_name=database_name_in,
                                    collection_name="analysis",
                                    query={"server_id": server_id},
                                    mongo_database_manager=mongo_database_manager)

        if not success:
            raise Exception("Failed to upsert tree")
        # markdown_string_with_summary_output = nested_dict_to_markdown(tree_dict=chat_tree_with_summary)
        # markdown_path_with_summary = Path(
        #     get_default_backup_save_path(filename="classbot_full_server_tree_with_summary",
        #                                  subfolder=database_name_in,
        #                                  filetype=".md"))
        # markdown_path_with_summary.write_text(markdown_string_with_summary_output, encoding="utf-8")

        save_chat_tree_to_markdown_directory(tree=chat_tree,
                                             directory_root=get_default_backup_save_path(
                                                 filename="classbot_chat_summaries_obsidian_vault",
                                                 filetype=None,
                                             ))
    except Exception as e:
        print(f"Ran into error: {e}")
        print(traceback.format_exc())
    finally:
        await mongo_database_manager.close()


if __name__ == "__main__":
    asyncio.run(run_summary_analysis())
