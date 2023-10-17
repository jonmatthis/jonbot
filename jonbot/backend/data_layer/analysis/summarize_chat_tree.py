import asyncio
from pathlib import Path
from typing import List

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from magic_tree.magic_tree_dictionary import MagicTreeDictionary

from jonbot import logger
from jonbot.backend.data_layer.analysis.get_server_chats import get_chats
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.system.path_getters import get_default_backup_json_save_path


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
This text represents a turn of conversation between a Human and an AI.
The human makes a statement, and the AI responds.
The full conversation involves a list of these turns.
Your job is to concisely summarize this turn in a way that will help another AI who can see the full list of ConversationTurnSummaries will have all of the information they need to understand the full conversation.
The main focus of this task is to understand the Human and their interests and goals.

Conversation Turn HumanMessage/AIResponse Pair:
+++
{text}
+++
"""


def summarize_text(text: str,
                   chunk_size: int = 1e4,
                   model: str = "gpt-3.5-turbo-16k") -> str:
    texts = split_text_into_chunks(model=model,
                                   chunk_size=chunk_size,
                                   text=text)

    llm = ChatOpenAI(temperature=0, model_name=model)
    prompt = ChatPromptTemplate.from_template(CONVERSATION_TURN_SUMMARIZER_PROMPT_TEMPLATE)
    chain = prompt | llm
    summaries = chain.batch([{"text": text} for text in texts])

    if len(summaries) > 1:
        logger.info(f"Summarized {len(texts)} texts into {len(summaries)} summaries")
        summary_texts = [summary["text"] for summary in summaries]
        summary = "\n".join(summary_texts)
        summarize_text(text=summary)
    else:
        summary = summaries[-1].content
        print(f"Original: \n {text} \n\n")
        print(f"Summary: \n {summary} \n\n")
        return summary


def get_chat_tree(chats: List[DiscordChatDocument]) -> MagicTreeDictionary:
    try:
        tree = MagicTreeDictionary()
        for chat in chats:
            context_tree_path = chat.context_route.as_tree_path
            for number, couplet in enumerate(chat.to_couplets()):
                tree[context_tree_path + [number]] = couplet.as_text
        return tree
    except Exception as e:
        logger.error(f"Error summarizing chat tree")
        logger.exception(e)
        raise e


if __name__ == "__main__":
    database_name = "classbot_database"
    server_id = 1150736235430686720
    chats_by_route = asyncio.run(get_chats(database_name=database_name,
                                           query={"server_id": server_id}))

    # save to json
    json_path = Path(get_default_backup_json_save_path(tag="classbot_chats_by_route"))
    chat_tree = get_chat_tree(chats=list(chats_by_route.values()))
    chat_tree.print_leaf_info()
    #
    # summary_tree = chat_tree.map_to_leaves(function=lambda leaf: summarize_text(text=leaf))
    # summary_tree_dict = summary_tree.__dict__
    # json_path = Path("summary_tree.json")
    # with open(json_path, "w") as f:
    #     json.dump(summary_tree_dict, f, indent=4)
    # print(summary_tree_dict)
    # f = 9
