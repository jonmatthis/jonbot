import asyncio
import logging
from pathlib import Path
from typing import Dict, Union, Any

from langchain.chat_models import ChatOpenAI
from langchain.vectorstores.chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

from jonbot.backend.data_layer.analysis.get_chats import get_chats
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.backend.data_layer.vector_embeddings.create_vector_store import get_or_create_vectorstore


logging.getLogger("chroma").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.INFO)



BASE_OUTLINE_DICT = {
    "The Neural Control of Real-World Human Movement": {
        "Nervous System and Human Movement": {
            "Cortex": {
                "Vision": {
                    "Retina": {},
                    "Oculomotor Control": {}
                },
                "Subcortical Structures": {
                    "Cerebellum": {},
                    "Brainstem": {}
                },
                "Spinal Cord": {
                    "Central Pattern Generators": {},
                    "Reflex Gating": {}
                },
                "Muscules": {
                    "Muscle Spindles": {},
                    "Golgi Bodies": {}
                }
            }
        },
        "Musculoskeletal Biomechanics": {
            "Center of Mass": {},
            "Center of Pressure": {}
        },
        "Jumping": {},
        "Clinical Applications": {},
        "Research Methods": {
            "Motion Capture": {},
            "Eye Tracking": {}
        }
    }
}


def to_snakecase(string):
    return string.lower().replace(" ", "_").replace("-", "_")


def dict_to_markdown(nested_dict, level=1):
    markdown_content = ""
    for key, value in nested_dict.items():
        # Create markdown header based on the current level
        markdown_content += ('#' * level) + ' ' + key + '\n\n'
        # If the key maps to a dictionary, recurse and increase the level
        if isinstance(value, dict):
            markdown_content += dict_to_markdown(value, level + 1)
    return markdown_content


def create_directories(base_path,
                       nested_dict) -> Dict[str, Any]:
    for key, value in nested_dict.items():
        if key == "path":
            continue
        try:
            # Convert the key to snake_case for the directory name
            dir_name = to_snakecase(key)
            dir_path = base_path / dir_name
            # Make the directory
            dir_path.mkdir(parents=True, exist_ok=True)
            if not "path" in nested_dict[key]:
                nested_dict[key]["path"] = str(dir_path)
            # If the value is a dict, recurse to create nested directories
            if isinstance(value, dict):
                create_directories(dir_path, value)
        except Exception as e:
            print(f"Error creating directory: {e}")

    return nested_dict


DOCUMENT_BUILDER_PROMPT_TEMPLATE = """ 
You are writing a professional level scientific review article on the topic of "The Neural Control of Real-World Human Movement".

You are currently writing the section titled "{section_title}".

You need to pull from the blob of text below (representing conversations between a student and a professor in the class) to write the section.

You need to write the section in the style of a professional scientific review article, with 2-3 relevant topic tags listed below the summary text, formatted in #kebab-case-hash-tags.

DO NOT MENTION THAT YOUR RAW TEXT IS A CONVERSATION BETWEEN A STUDENT AND A PROFESSOR. DO NOT MENTION ANYBODY'S NAME.

ONLY USE THE TEXT as a repository of information to pull from 

DO NOT INCLUDE AN INTRODUCTION SECTION or a CONCLUSION SECTION. 

Do not include any other text in your response other than the section you are writing.

Here is the text you are using to write the section:

+++
{text}
+++

REMEMBER: 

You are writing a professional level scientific review article on the topic of "The Neural Control of Real-World Human Movement".

You are currently writing the section titled "{section_title}".

You need to pull from the blob of text below (representing conversations between a student and a professor in the class) to write the section.

You need to write the section in the style of a professional scientific review article, with 5-10 relevant topic tags listed below the summary text, formatted in #kebab-case-hash-tags.

DO NOT MENTION THAT YOUR RAW TEXT IS A CONVERSATION BETWEEN A STUDENT AND A PROFESSOR. DO NOT MENTION ANYBODY'S NAME.

ONLY USE THE TEXT as a repository of information to pull from

DO NOT INCLUDE AN INTRODUCTION SECTION or a CONCLUSION SECTION. 

Do not include any other text in your response other than the section you are writing.
"""


def document_builder_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(DOCUMENT_BUILDER_PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain



FORMATTING_CHAIN_PROMPT_TEMPLATE = """
Format this text so it matches the style of a professional scientific review article, formatted as a markdown document with tags beneath each section

+++
{text}
+++

The document should roughly follow this schema

```
# Document title
## Section Title
text text text
### Subsection Title
text text text

# Topic Tags
#kebab-case-hash-tags1
#kebab-case-hash-tags2
#kebab-case-hash-tags3
```

"""


def formatting_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    prompt = ChatPromptTemplate.from_template(FORMATTING_CHAIN_PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain


def generate_document_from_string(string: str) -> str:
    chain = document_builder_chain()
    return chain.invoke(input=string)


def get_relevant_text(query_string: str,
                      vector_store: Chroma,
                      chats: Dict[str, DiscordChatDocument],
                      number_of_docs: int = 10,
                      max_length: int = 10000) -> str:
    relevant_documents = vector_store.similarity_search(query_string, number_of_docs=number_of_docs)
    # randomize the order of the documents
    import random
    random.shuffle(relevant_documents)

    relevant_text = ""
    for document in relevant_documents:
        chat_id = document.metadata["chat_id"]
        chat_id_key = str({"chat_id": chat_id})
        relevant_text += chats[chat_id_key].as_text + "\n\n"
        if len(relevant_text) > max_length:
            relevant_text = relevant_text[:max_length]
            break
    return relevant_text


def generate_document_from_outline(outline: Dict[str, Union[Dict[str, Any], str]],
                                   vector_store: Chroma,
                                   chats: Dict[str, DiscordChatDocument],
                                   save_directory: Path,
                                   levels=3) -> str:
    # Create the directories
    create_directories(save_directory, outline)

    document_chain = document_builder_chain()
    format_chain = formatting_chain()

    def recurse_outline(outline: Dict[str, Union[Dict[str, Any], str]]) -> Dict[str, Union[Dict[str, Any], str]]:
        for key, value in outline.items():
            if isinstance(value, dict):
                relevant_text = get_relevant_text(query_string=key,
                                                  vector_store=vector_store,
                                                  chats=chats)
                text_out = document_chain.invoke(input={"text": relevant_text,
                                                        "section_title": key})
                # print(f"Generated text for section {key}: {text_out.content}")
                formatted_text = format_chain.invoke(input={"text": text_out})
                # print(f"Formatted text for section {key}: {formatted_text.content}")
                document_save_path = Path(value["path"]) / f"{key}.md"
                with open(document_save_path, "w", encoding="utf-8") as f:
                    f.write(formatted_text.content)
                print(f"Saved document to {document_save_path}")
                recurse_outline(value)

    recurse_outline(outline)


if __name__ == "__main__":
    database_name_in = "classbot_database"
    server_id_outer = 1150736235430686720
    vector_store = asyncio.run(get_or_create_vectorstore(chroma_collection_name="classbot_vector_store",
                                                         chroma_persistence_directory="classbot_chroma_persistence",
                                                         server_id=server_id_outer,
                                                         database_name=database_name_in
                                                         ))
    chats_out = asyncio.run(get_chats(database_name=database_name_in,
                                      query={"server_id": server_id_outer}))
    chat_documents = {key: DiscordChatDocument.from_dict(chat_dict) for key, chat_dict in chats_out.items()}

    save_directory_outer = Path(
        r"C:\Users\jonma\syncthing_folders\jon_main_syncthing\jonbot_data\classbot_database\final_paper")
    save_directory_outer.mkdir(exist_ok=True, parents=True)
    generate_document_from_outline(outline=BASE_OUTLINE_DICT,
                                   vector_store=vector_store,
                                   chats=chat_documents,
                                   save_directory=save_directory_outer)
