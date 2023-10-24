import asyncio
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Coroutine, Hashable

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


CONVERSATION_TURN_SUMMARIZER_PROMPT_TEMPLATE = """
Summarize this conversation:

+++
{text}
+++
"""


def clean_dictionary(d):
    new_dict = {}

    for key, value in d.items():
        if isinstance(value, dict):
            value = clean_dictionary(value)
        elif hasattr(value, "to_dict"):
            value = value.to_dict()
        elif hasattr(value, "dict"):
            value = value.dict()
        elif isinstance(value, Path):
            value = str(value)
        else:
            try:
                json.dumps(value)
            except TypeError:
                raise TypeError(f"Value for key: {key} is not JSON serializable: {value}")
        new_dict[key] = value

    return new_dict


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


async def summarize_text(text: str) -> str:
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(CONVERSATION_TURN_SUMMARIZER_PROMPT_TEMPLATE)
    chain = prompt | llm
    summary = await chain.ainvoke(input={"text": text})
    return summary.content


async def add_summary_to_chat_tree(tree_dict: Dict[str, Any], tasks: List[Coroutine] = None) -> Dict[str, Any]:
    if tasks is None:
        tasks = []
    for key, value in tree_dict.items():
        if isinstance(value, dict) and key != "chat":
            asyncio.create_task(add_summary_to_chat_tree(tree_dict=value, tasks=tasks))
        else:
            summary = asyncio.create_task(summarize_text(text=value["text"]))
            value["summary"] = summary

    return tree_dict


async def summarize_leaves(tree: MagicTreeDictionary, leaf_key: Hashable) -> MagicTreeDictionary:
    text_paths = tree.get_paths_to_keys(keys=[leaf_key])

    text_inputs = [{"text": tree[path]} for path in text_paths[:10]]

    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(CONVERSATION_TURN_SUMMARIZER_PROMPT_TEMPLATE)
    chain = prompt | llm
    summaries = await chain.abatch(inputs=text_inputs)

    # Create dictionary with text_paths as keys and summaries as values
    for path, summary in zip(text_paths, summaries):
        tree[path[:-1]]["summary"] = {"content": summary.content,
                                      "stats": {"original_length": len(tree[path]),
                                                "summary_length": len(summary.content)}}

    return tree


async def upsert_tree(tree: MagicTreeDictionary,
                      database_name: str,
                      collection_name: str,
                      query: dict,
                      mongo_database_manager: MongoDatabaseManager) -> bool:
    return await mongo_database_manager.upsert_one(database_name=database_name,
                                                   collection_name=collection_name,
                                                   data=clean_dictionary(tree.to_dict()),
                                                   query=query)


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
                json.dumps({chat_id: chat.dict() for chat_id, chat, in chats_by_id.items()}, indent=4), encoding="utf-8")

        chat_tree = MagicTreeDictionary()
        for chat_id, chat in chats_by_id.items():
            if not isinstance(chat, DiscordChatDocument):
                chat = DiscordChatDocument(**chat.dict())
            tree_path = chat.context_route.as_friendly_tree_path
            chat_tree[tree_path]["chat"]["text"] = chat.as_text
            chat_tree[tree_path]["chat"]["speakers"] = "\n\n".join([f'{speaker}' for speaker in chat.speakers])
            for couplet_number, couplet in enumerate(chat.couplets):
                chat_tree[tree_path]["chat"]["couplets"][couplet_number] = couplet.text

        chat_tree_dict = chat_tree.dict()
        chat_tree_dict = clean_dictionary(chat_tree_dict)
        chat_tree_json_path = Path(get_default_backup_save_path(filename="classbot_chats_tree",
                                                                subfolder=database_name_in))
        chat_tree_json_path.write_text(json.dumps(chat_tree_dict, indent=4), encoding="utf-8")

        markdown_string_output = nested_dict_to_markdown(tree_dict=chat_tree_dict)
        markdown_path = Path(get_default_backup_save_path(filename="classbot_full_server_tree",
                                                          subfolder=database_name_in,
                                                          filetype=".md"))
        markdown_path.write_text(markdown_string_output, encoding="utf-8")

        chat_tree_with_summary = await summarize_leaves(tree=chat_tree, leaf_key="text")
        # chat_tree_with_summary = asyncio.run(add_summary_to_chat_tree(tree_dict=chat_tree_dict))

        chat_tree_with_summary_json_path = Path(get_default_backup_save_path(filename="classbot_chats_tree_with_summary",
                                                                             subfolder=database_name_in))
        chat_tree_with_summary_json_path.write_text(json.dumps(clean_dictionary(chat_tree_with_summary.dict()), indent=4),
                                                    encoding="utf-8")

        await upsert_tree(tree=chat_tree_with_summary,
                          database_name=database_name_in,
                          collection_name="analysis",
                          query={"server_id": server_id},
                          mongo_database_manager=mongo_database_manager)

        markdown_string_with_summary_output = nested_dict_to_markdown(tree_dict=chat_tree_with_summary)
        markdown_path_with_summary = Path(get_default_backup_save_path(filename="classbot_full_server_tree_with_summary",
                                                                       subfolder=database_name_in,
                                                                       filetype=".md"))
        markdown_path_with_summary.write_text(markdown_string_with_summary_output, encoding="utf-8")
    except Exception as e:
        print(f"Ran into error: {e}")
        print(traceback.format_exc())
    finally:
        await mongo_database_manager.close()

if __name__ == "__main__":
    asyncio.run(run_summary_analysis())
