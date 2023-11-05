import asyncio
import time
import traceback
from typing import List, Dict, Any

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from magic_tree.magic_tree_dictionary import MagicTreeDictionary

from jonbot.backend.data_layer.analysis.get_chats import get_chats
from jonbot.backend.data_layer.analysis.summarize_chats.print_results_as_markdown import save_all_results_to_markdown
from jonbot.backend.data_layer.database.get_mongo_database_manager import get_mongo_database_manager
from jonbot.backend.data_layer.database.mongo_database import MongoDatabaseManager
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

Your response should of a comma separated list of topics wrapped in [[double brackets]] like this: 

```markdown
[[Topic Name]], [[Another topic name]], [[Yet another topic name]]

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

CONTEXT_PAPER_DOCUMENT_GENERATOR_PROMPT = """
You are an AI teaching assistant for a class called "The Neural Control of Real World Human Movement", analyzing a
collection of extracted tags and/or summaries based on conversations between students and an AI teaching assistant in order 
to generate a paper that summarizes the most important topics discussed in this context.

You will use the information in the extracted tags and/or summaries to generate a paper that summarizes the most important 
topics discussed in this context.

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


Your reponse should consist of heirarchically organized outline formatted with markdown headers with the titles wrapped in 
[[double brackets]]  and a bulleted outline of information relevant to the topic like this:

```markdown
# [[Topic Name]]
- Some Information 
    - About this
        - Topic
## [[Sub Topic Name]]
- Some Information
    - about this topic
- Still more information
### [[Sub Sub Topic Name]]
- more writing about this topic
- and so on
```

++++


Here is the extracted tags and/or summaries:

+++
{text}
+++

DO NOT MAKE THINGS UP! ONLY USE INFORMATION THAT IS PROVIDED TO YOU.  CITE YOUR SOURCES WHEN POSSIBLE. 
"""


def create_simple_summary_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(SIMPLE_CONVERSATION_SUMMARIZER_PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain


def create_topic_extractor_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(TOPIC_EXTRACTOR_PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain


def create_global_topic_tree_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k", max_tokens=1e3)
    # llm = ChatAnthropic(temperature=0, model="claude-v1", max_tokens=5e3)
    prompt = ChatPromptTemplate.from_template(GLOBAL_TOPIC_TREE_PROMPT)
    chain = prompt | llm
    return chain


def create_context_paper_document_generator_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k", max_tokens=1e3)
    # llm = ChatAnthropic(temperature=0, model="claude-v1", max_tokens=5e3)
    prompt = ChatPromptTemplate.from_template(CONTEXT_PAPER_DOCUMENT_GENERATOR_PROMPT)
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


async def generate_context_document(chats: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    all_results = {}
    chain = create_context_paper_document_generator_chain()

    all_topics = [f"{chat['metadata']['topics']}\n\n==========\n\n" for chat in chats.values()]
    all_topics_str = "\n".join(all_topics)
    results = await chain.ainvoke({"text": all_topics_str})

    all_results["from_topics"] = {"input": all_topics_str,
                                  "result": results.content}

    all_summaries = [f"{chat['metadata']['simple_summary']}\n\n==========\n\n" for chat in chats.values()]
    all_summaries_str = "\n".join(all_summaries)
    all_summaries_chunks = split_text_into_chunks(text=all_summaries_str, model="gpt-3.5-turbo-16k",
                                                  chunk_size=int(1.3e4))
    all_results["from_summaries"] = {"input": all_summaries_str,
                                     "result": await handle_text_chunks(chain, all_summaries_chunks)}

    all_summaries_and_tags = [
        f"{chat['metadata']['simple_summary']}\n{chat['metadata']['topics']}\n==========\n\n"
        for chat in chats.values()]
    all_summaries_and_tags_str = "\n".join(all_summaries_and_tags)
    all_summaries_and_tags_chunks = split_text_into_chunks(text=all_summaries_and_tags_str, model="gpt-3.5-turbo-16k",
                                                           chunk_size=int(1e4))
    all_results["from_summaries_and_tags"] = {"input": all_summaries_and_tags_str,
                                              "result": await handle_text_chunks(chain,
                                                                                 all_summaries_and_tags_chunks)}

    return all_results


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
                                   query: Dict = None,
                                   ):
    if not query:
        query = {}
    chats_by_id = await get_chats(mongo_database_manager=mongo_database_manager,
                                  database_name=database_name,
                                  collection_name="chats",
                                  query=query)

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
                                  query: Dict = None,
                                  collection_name: str = "analysis_chats"
                                  ) -> Dict[str, Dict[str, Dict[str, Any]]]:
    if not query:
        query = {}

    chats_by_server_id = await get_chats(mongo_database_manager=mongo_database_manager,
                                         database_name=database_name,
                                         collection_name=collection_name,
                                         query=query)
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
                               query: Dict = None,
                               analyze_chats_bool=True,
                               ):
    mongo_database_manager = await get_mongo_database_manager()

    if query is None:
        query = {}
    all_results = {}
    try:
        if analyze_chats_bool:
            await analyze_individual_chats(mongo_database_manager=mongo_database_manager,
                                           database_name=database_name,
                                           query=query, )

        chats_by_index_type = await get_chats_by_index_type(
            mongo_database_manager=mongo_database_manager,
            database_name=database_name,
            collection_name="analysis_chats",
            query=query)

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

                all_results[index_type][f"{index_name}:{index_id}_topic_trees"] = await calculate_global_topic_tree(
                    chats=chats)
                await mongo_database_manager.upsert_one(database_name=database_name,
                                                        collection_name="analysis_global",
                                                        data=all_results[index_type][
                                                            f"{index_name}:{index_id}_topic_trees"],
                                                        query={"server_id": CLASSBOT_SERVER_ID})

                all_results[index_type][
                    f"{index_name}:{index_id}_document"] = await generate_context_document(chats=chats)
                await mongo_database_manager.upsert_one(database_name=database_name,
                                                        collection_name="analysis_document",
                                                        data=all_results[index_type][
                                                            f"{index_name}:{index_id}_document"],
                                                        query={"server_id": CLASSBOT_SERVER_ID})

            save_all_results_to_markdown(all_results=all_results,
                                         directory_root=get_default_backup_save_path(
                                             filename="classbot_all_results",
                                             filetype=None,
                                         ),
                                         index_type=index_type,
                                         )

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
                                     ),
                                     index_type=index_type,
                                     )
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
    asyncio.run(run_summary_analysis(query={"server_id": 1150736235430686720},
                                     analyze_chats_bool=True,
                                     )
                )
