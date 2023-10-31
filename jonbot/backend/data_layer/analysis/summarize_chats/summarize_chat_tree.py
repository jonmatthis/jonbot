import asyncio
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Hashable

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from magic_tree.magic_tree_dictionary import MagicTreeDictionary

from jonbot.backend.data_layer.analysis.get_chats import get_chats
from jonbot.backend.data_layer.analysis.summarize_chats.print_results_as_markdown import save_all_results_to_markdown
from jonbot.backend.data_layer.database.get_mongo_database_manager import get_mongo_database_manager
from jonbot.backend.data_layer.database.mongo_database import MongoDatabaseManager
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.system.environment_variables import CLASSBOT_SERVER_ID


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

TOPIC_EXTRACTOR_PROMPT_TEMPLATE = """
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

Below is a conversation between a student in the class and an AI teaching assistant.

Your job is to extract tags for the course-relevant topics that are discussed in this conversation.

Your response should consist of heirarchically organized outline formatted like this: 

```markdown
# [[Topic Name]]
## [[Sub Topic Name]]
### [[Sub Sub Topic Name]]
... and as many deeper layers as you need
```

Here is the conversation:

+++
{text}
+++
"""

GLOBAL_TOPIC_TREE_PROMPT = """
You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement", analyzing a
 collection of extracted tags and/or summaries based on conversations between students and an AI teaching assistant.

Here is a description of this class:

=====
COURSE DESCRIPTION

Students will explore the neural basis of natural human behavior in real-world contexts (e.g., sports, dance, or 
everyday-activities) by investigating the neural-control of full-body human-movement. The course will cover 
philosophical, technological, and scientific aspects related to the study of natural-behavior while emphasizing  
ands-on, project-based learning. Students will use free-open-source-software, and artificial-intelligence, 
machine-learning and computer-vision driven tools and methods to record human movement in unconstrained environments. 
======

Your job is to extract tags for the course-relevant topics that are discussed in this conversation.


Your reponse should consist of heirarchically organized outline formatted like this: 

```markdown
# [[Topic Name]]
## [[Sub Topic Name]]
### [[Sub Sub Topic Name]]
#### [[Sub Sub Sub Topic Name]]
... and as many deeper layers as you need
```

++++


Here is the extracted tags and/or summaries:

+++
{text}
+++
"""


def create_global_topic_tree_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k", max_tokens=1e3)
    # llm = ChatAnthropic(temperature=0, model="claude-v1", max_tokens=5e3)
    prompt = ChatPromptTemplate.from_template(GLOBAL_TOPIC_TREE_PROMPT)
    chain = prompt | llm
    return chain


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


def save_chats_to_markdown_directory(chats_by_id: Dict[str, DiscordChatDocument],
                                     directory_root: str):
    root_path = Path(directory_root)
    for chats_by_id in chats_by_id:
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


#


async def analyze_chats(chats: Dict[str, Dict[str, Any]],
                        target_key: str,
                        result_key: str,
                        chains: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    try:

        for chain_name, chain in chains.items():
            if isinstance(chain, dict):
                parser = chain["parser"]
                chain = chain["chain"]
            else:
                parser = None

            text_inputs = []
            for chat in chats.values():
                if target_key == "text":
                    text_inputs.append({"text": chat["as_text"]})
                else:
                    if target_key in chat["metadata"].keys():
                        text_inputs.append({"text": chat["metadata"][target_key]})
                    elif target_key in chat.keys():
                        text_inputs.append({"text": chat[target_key]})
                    else:
                        raise ValueError(f"Could not find target key {target_key} in chat {chat}")

            # send batches in chunks to avoid rate limits
            results = []
            chunk_size = 20
            text_input_chunks = [text_inputs[i:i + chunk_size] for i in range(0, len(text_inputs), chunk_size)]

            # make sure we got all of them
            total_inputs = 0
            for chunk in text_input_chunks:
                total_inputs += len(chunk)
            assert total_inputs == len(text_inputs), "Lost some inputs in chunking..."

            for chunk in text_input_chunks:
                results.extend(await chain.abatch(inputs=chunk))
                time.sleep(2.0)

            for key, result in zip(chats.keys(), results):
                if parser:
                    content = result.content
                    content.replace("TOPICS:\n", "").replace(",", ",\n")
                #     parsed_result = parser.invoke(result)
                if not "metadata" in chats[key].keys():
                    chats[key]["metadata"] = {}
                chats[key]["metadata"][result_key] = result.content
    except Exception as e:
        print(f"Failed to analyze leaves: {e}")
        raise e
    return chats


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


def get_all_tags(tree: MagicTreeDictionary):
    paths = tree.get_paths_to_keys(keys=["topics"])
    all_tags = []
    for path in paths:
        all_tags.extend(tree[path])
    return all_tags


async def handle_text_chunks(chain, text_chunks: List[str]) -> str:
    results_chunks = []
    for chunk in text_chunks:
        results_chunks.append(await chain.ainvoke({"text": chunk}))
    if len(results_chunks) > 1:
        results = [result.content for result in results_chunks]
        results = "\n".join(results)
        results = await chain.ainvoke({"text": results})
    else:
        results = results_chunks[0]
    return results.content


async def calculate_global_topic_tree(chats: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    all_results = {}
    global_topic_tree_chain = create_global_topic_tree_chain()

    all_topics = [f"{chat['metadata']['topics']}\n\n==========\n\n" for chat in chats.values()]
    all_topics_str = "\n".join(all_topics)
    results = await global_topic_tree_chain.ainvoke({"text": all_topics_str})

    all_results["from_topics"] = {"input": all_topics_str,
                                  "result": results.content}

    all_summaries = [f"{chat['metadata']['simple_summary']}\n\n==========\n\n" for chat in chats.values()]
    all_summaries_str = "\n".join(all_summaries)
    all_summaries_chunks = split_text_into_chunks(text=all_summaries_str, model="gpt-3.5-turbo-16k",
                                                  chunk_size=int(1.3e4))
    all_results["from_summaries"] = {"input": all_summaries_str,
                                     "result": await handle_text_chunks(global_topic_tree_chain, all_summaries_chunks)}

    all_summaries_and_tags = [
        f"{chat['metadata']['simple_summary']}\n{chat['metadata']['topics']}\n==========\n\n"
        for chat in chats.values()]
    all_summaries_and_tags_str = "\n".join(all_summaries_and_tags)
    all_summaries_and_tags_chunks = split_text_into_chunks(text=all_summaries_and_tags_str, model="gpt-3.5-turbo-16k",
                                                           chunk_size=int(1e4))
    all_results["from_summaries_and_tags"] = {"input": all_summaries_and_tags_str,
                                              "result": await handle_text_chunks(global_topic_tree_chain,
                                                                                 all_summaries_and_tags_chunks)}

    return all_results


async def analyze_individual_chats(mongo_database_manager: MongoDatabaseManager,
                                   database_name: str,
                                   server_id: int,
                                   ):
    chats_by_id = await get_chats(mongo_database_manager=mongo_database_manager,
                                  database_name=database_name,
                                  collection_name="chats",
                                  query={"server_id": server_id})

    simple_summary_chain = {"simple_summary": create_simple_summary_chain()}
    chats_by_id = await analyze_chats(chats=chats_by_id,
                                      target_key="text",
                                      result_key="simple_summary",
                                      chains=simple_summary_chain)
    topics_chain = {"topics": create_topic_extractor_chain()}
    # "parser": PydanticOutputParser(pydantic_object=TopicTags)}
    chats_by_id = await analyze_chats(chats=chats_by_id,
                                      target_key="text",
                                      result_key="topics",
                                      chains=topics_chain)
    await upsert_chats(chats_by_id=chats_by_id,
                       database_name=database_name,
                       collection_name="analysis_chats",
                       mongo_database_manager=mongo_database_manager)

    return chats_by_id


async def get_chats_by_index_type(mongo_database_manager: MongoDatabaseManager,
                                  database_name: str,
                                  server_id: int,
                                  collection_name: str = "analysis_chats"
                                  ) -> Dict[str, Dict[str, Dict[str, Any]]]:
    chats_by_server_id = await get_chats(mongo_database_manager=mongo_database_manager,
                                         database_name=database_name,
                                         collection_name=collection_name,
                                         query={"server_id": server_id})
    print(f"Found {len(chats_by_server_id)} total chats...")
    all_category_ids = set([chat["category_id"] for chat in chats_by_server_id.values()])
    print(f"Found {len(all_category_ids)} total category ids...")
    chats_by_category_id = {}
    for category_id in all_category_ids:
        chats_by_category_id[category_id] = await get_chats(mongo_database_manager=mongo_database_manager,
                                                            database_name=database_name,
                                                            collection_name=collection_name,
                                                            query={"category_id": category_id})

    all_channel_ids = set([chat["channel_id"] for chat in chats_by_server_id.values()])
    print(f"Found {len(all_channel_ids)} total channel ids...")
    chats_by_channel_id = {}
    for channel_id in all_channel_ids:
        chats_by_channel_id[channel_id] = await get_chats(mongo_database_manager=mongo_database_manager,
                                                          database_name=database_name,
                                                          collection_name=collection_name,
                                                          query={"channel_id": channel_id})
    all_owner_ids = set([chat["owner_id"] for chat in chats_by_server_id.values()])
    print(f"Found {len(all_owner_ids)} total owner ids...")
    chats_by_owner_id = {}
    for owner_id in all_owner_ids:
        chats_by_owner_id[owner_id] = await get_chats(mongo_database_manager=mongo_database_manager,
                                                      database_name=database_name,
                                                      collection_name=collection_name,
                                                      query={"owner_id": owner_id})
    chats_by_index_type = {
        "channel": chats_by_channel_id,
        "category": chats_by_category_id,
        "owner": chats_by_owner_id,
        "server": chats_by_server_id,
    }
    return chats_by_index_type


async def run_summary_analysis(subset_size: int = -1,
                               database_name: str = "classbot_database",
                               server_id: int = CLASSBOT_SERVER_ID):
    mongo_database_manager = await get_mongo_database_manager()

    all_results = {}
    try:
        # await analyze_individual_chats(mongo_database_manager=mongo_database_manager,
        #                                database_name=database_name,
        #                                server_id=server_id)

        chats_by_index_type = await get_chats_by_index_type(
            mongo_database_manager=mongo_database_manager,
            database_name=database_name,
            collection_name="analysis_chats",
            server_id=server_id)

        for index_type, chats_by_index_id in chats_by_index_type.items():
            print("\n\n========================\n\n")
            print(f"Analyzing {index_type} chats...")
            print("\n\n========================\n\n")

            all_results[index_type] = {}
            for index_id, chats in chats_by_index_id.items():
                if 0 in chats.keys():
                    del chats[0]
                if '0' in chats.keys():
                    del chats['0']

                index_name_key = f"{index_type}_name"
                index_name = ""
                for value in chats.values():
                    if index_name_key in value.keys():
                        index_name = value[index_name_key]
                        break

                all_results[index_type][f"{index_name}:{index_id}"] = await calculate_global_topic_tree(chats=chats)
                await mongo_database_manager.upsert_one(database_name=database_name,
                                                        collection_name="analysis_global",
                                                        data=all_results[index_type][f"{index_name}:{index_id}"],
                                                        query={"server_id": CLASSBOT_SERVER_ID})

            await mongo_database_manager.upsert_one(database_name=database_name,
                                                    collection_name="analysis_global",
                                                    data=all_results[index_type],
                                                    query={"server_id": CLASSBOT_SERVER_ID})
        await mongo_database_manager.upsert_one(database_name=database_name,
                                                collection_name="analysis_global",
                                                data=all_results[index_type],
                                                query={"server_id": CLASSBOT_SERVER_ID})

        save_all_results_to_markdown(all_results=all_results,
                                     directory_root=get_default_backup_save_path(
                                         filename="classbot_all_results",
                                         filetype=None,
                                     ))
        # save_chats_to_markdown_directory(chats_by_id=selected_chats_by_id,
        #                                  directory_root=get_default_backup_save_path(
        #                                      filename="classbot_chat_summaries_obsidian_vault",
        #                                      filetype=None,
        #                                  ))
    except Exception as e:
        print(f"Ran into error: {e}")
        print(traceback.format_exc())
    finally:
        await mongo_database_manager.close()


if __name__ == "__main__":
    asyncio.run(run_summary_analysis())
