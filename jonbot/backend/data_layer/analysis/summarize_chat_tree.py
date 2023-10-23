from pathlib import Path
from typing import List, Dict, Any

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from magic_tree.magic_tree_dictionary import MagicTreeDictionary

from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
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
#
# =========
# ## Course Title
# Neural Control of Real World Human Movement
#
# ## Course Description
# Students will explore the neural basis of natural human behavior in real-world contexts (e.g., [sports], [dance], or
# [everyday-activities]) by investigating the [neural-control] of [full-body] [human-movement]. The course will cover
# [philosophical], [technological], and [scientific] aspects related to the study of [natural-behavior] while emphasizing
#  hands-on, project-based learning. Students will use [free-open-source-software], and [artificial-intelligence],
#  [machine-learning] and [computer-vision] driven tools and methods to record human movement in unconstrained
#  environments.
#
# The course promotes interdisciplinary collaboration and introduces modern techniques for decentralized
# [project-management], [AI-assisted-research-techniques], and [Python]-based programming
# (No prior programming experience is required). Students will receive training in the use of AI technology for
# project management and research conduct, including [literature-review], [data-analysis], [data-visualization],
# and [presentation-of-results]. Through experiential learning, students will develop valuable skills in planning and
# executing technology-driven research projects while examining the impact of structural inequities on scientific
# inquiry.
#
#
# ## Course Objectives
# - Gain exposure to key concepts related to neural control of human movement.
# - Apply interdisciplinary approaches when collaborating on complex problems.
# - Develop a basic understanding of machine-learning tools for recording human movements.
# - Contribute effectively within a team setting towards achieving common goals.
# - Acquire valuable skills in data analysis or background research.
#
# ==============
#
# The human makes a statement, and the AI responds.
# The main focus of this task is to understand the Human and their interests and goals.
#
# Include a "topic list" at the end of your summary, which is a list of the [square bracketed] topics that
#  were mentioned in the course description
#
# Your output should look like:
#
# SUMMARY:
# ((summarize the conversation, e.g. "The human asked about the musculoskeletal system, and the AI responded
# with information about the musculoskeletal system. From there the human asked about clinical applications of
# the musculoskeletal system, and the AI responded with information about clinical applications of the
# musculoskeletal system and the AI mentioned some information about orthopedic surgery"))
#
# TOPICS:
# - [topic1]
# - [topic2]
# - [topic3]
#
# Conversation Turn HumanMessage/AIResponse Pair:
# +++
# {text}
# +++
# """

# def summarize_text(text: str,
#                    chunk_size: int = 1e4,
#                    model: str = "gpt-3.5-turbo-16k") -> str:
#
#     llm = ChatOpenAI(temperature=0, model_name=model)
#     prompt = ChatPromptTemplate.from_template(CONVERSATION_TURN_SUMMARIZER_PROMPT_TEMPLATE)
#     chain = prompt | llm
#     summary = chain.ainvoke(input={"text": text})
#
#     if len(summaries) > 1:
#         logger.info(f"Summarized {len(texts)} texts into {len(summaries)} summaries")
#         summary_texts = [summary["text"] for summary in summaries]
#         summary = "\n".join(summary_texts)
#         summarize_text(text=summary)
#     else:
#         summary = summaries[-1].content
#         print(f"Original: \n {text} \n\n")
#         print(f"Summary: \n {summary} \n\n")
#         return summary


#
# def get_chat_tree(chats: List[DiscordChatDocument]) -> MagicTreeDictionary:
#     try:
#         tree = MagicTreeDictionary()
#         for chat in chats:
#             context_tree_path = chat.context_route.as_tree_path
#             for number, couplet in enumerate(chat.couplets):
#                 tree[context_tree_path + [number]] = couplet.text
#         return tree
#     except Exception as e:
#         logger.error(f"Error summarizing chat tree")
#         logger.exception(e)
#         raise e


import json


def clean_dictionary(d):
    new_dict = {}

    for k, v in d.items():
        if isinstance(v, dict):
            v = clean_dictionary(v)
        else:
            try:
                json.dumps(v)
            except TypeError:
                raise TypeError(f"Value for key: {k} is not JSON serializable: {v}")
        new_dict[k] = v

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


def summarize_text(text: str) -> str:
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(CONVERSATION_TURN_SUMMARIZER_PROMPT_TEMPLATE)
    chain = prompt | llm
    summary = chain.invoke(input={"text": text})
    return summary.content


def add_summary_to_chat_tree(tree_dict: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in tree_dict.items():
        if isinstance(value, dict) and key != "chat":
            add_summary_to_chat_tree(tree_dict=value)
        else:
            summary = summarize_text(text=value["text"])
            value["summary"] = summary
    return tree_dict


if __name__ == "__main__":
    database_name = "classbot_database"
    server_id = 1150736235430686720
    json_path = Path(get_default_backup_save_path(filename="classbot_chats_by_chat_id",
                                                  subfolder=database_name))
    # chats_by_id = asyncio.run(get_chats(database_name=database_name,
    #                                        query={"server_id": server_id}))
    # # save to json

    # chats_serializable = {}
    # for chat_id, chat in chats_by_id.items():
    #     chats_serializable[chat_id] = chat.dict()
    # json_path.write_text(json.dumps(chats_serializable, indent=4), encoding="utf-8")

    chats_by_id = json.loads(json_path.read_text(encoding="utf-8"))
    chat_tree = MagicTreeDictionary()
    for chat_id, chat in chats_by_id.items():
        if not isinstance(chat, DiscordChatDocument):
            chat = DiscordChatDocument(**chat)
        tree_path = chat.context_route.as_friendly_tree_path
        chat_tree[tree_path]["chat"]["text"] = chat.as_text
        chat_tree[tree_path]["chat"]["speakers"] = "\n\n".join([f'{speaker}' for speaker in chat.speakers])

    chat_tree_dict = chat_tree.dict()
    chat_tree_dict = clean_dictionary(chat_tree_dict)
    chat_tree_json_path = Path(get_default_backup_save_path(filename="classbot_chats_tree",
                                                            subfolder=database_name))
    chat_tree_json_path.write_text(json.dumps(chat_tree_dict, indent=4), encoding="utf-8")

    markdown_string_output = nested_dict_to_markdown(tree_dict=chat_tree_dict)
    markdown_path = Path(get_default_backup_save_path(filename="classbot_full_server_tree",
                                                      subfolder=database_name,
                                                      filetype=".md"))
    markdown_path.write_text(markdown_string_output, encoding="utf-8")

    chat_tree_with_summary = add_summary_to_chat_tree(tree_dict=chat_tree_dict)
    chat_tree_with_summary_json_path = Path(get_default_backup_save_path(filename="classbot_chats_tree_with_summary",
                                                                         subfolder=database_name))
    chat_tree_with_summary_json_path.write_text(json.dumps(chat_tree_with_summary, indent=4), encoding="utf-8")
    markdown_string_with_summary_output = nested_dict_to_markdown(tree_dict=chat_tree_with_summary)
    markdown_path_with_summary = Path(get_default_backup_save_path(filename="classbot_full_server_tree_with_summary",
                                                                   subfolder=database_name,
                                                                   filetype=".md"))
    markdown_path_with_summary.write_text(markdown_string_with_summary_output, encoding="utf-8")

    f = 9
    #
    # summary_tree = chat_tree.map_to_leaves(function=lambda leaf: summarize_text(text=leaf))
    # summary_tree_dict = summary_tree.__dict__
    # json_path = Path("summary_tree.json")
    # with open(json_path, "w") as f:
    #     json.dump(summary_tree_dict, f, indent=4)
    # print(summary_tree_dict)
    # f = 9
