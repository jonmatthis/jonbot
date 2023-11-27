import asyncio
from pathlib import Path
from typing import Dict

from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import Chroma

from jonbot.backend.data_layer.analysis.get_chats import get_chats
from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument


async def create_vector_store(chats: Dict[str, DiscordChatDocument], run_embeddings: bool = False):
    print("Creating vector store from {collection_name} collection with {len(all_entries)} entries")
    documents_by_couplet = []
    documents_by_chat = []
    for chat in chats.values():
        # get the first non-bot speaker
        speaker_id = 0
        for speaker in chat.speakers:
            if not speaker.type == "bot":
                speaker_id = speaker.id

        documents_by_chat.append(Document(page_content=chat.as_text,
                                          metadata={"source": chat.jump_url,
                                                    "chat_id": chat.thread_id,
                                                    "speaker_id": speaker_id,
                                                    "context_description": chat.context_description,
                                                    **chat.context_route.as_flat_dict,
                                                    }
                                          )
                                 )
        for couplet_number, couplet in enumerate(chat.couplets):
            if couplet.as_text == "":
                continue
            documents_by_couplet.append(Document(page_content=couplet.as_text,
                                                 metadata={"source": chat.jump_url,
                                                           "couplet_number": couplet_number,
                                                           "chat_id": chat.thread_id,
                                                           "speaker_id": speaker_id,
                                                           "context_description": chat.context_description,
                                                           **chat.context_route.as_flat_dict,
                                                           }
                                                 )
                                        )

    chat_vector_store_collection_name = "chat_vector_store"
    chat_vector_store_persist_directory = str(Path("./chroma") / chat_vector_store_collection_name)

    couplet_vector_store_collection_name = "couplet_vector_store"
    couplet_vector_store_persist_directory = str(Path("./chroma") / couplet_vector_store_collection_name)

    if run_embeddings:
        chat_vector_store = Chroma.from_documents(
            documents=documents_by_chat,
            embedding=OpenAIEmbeddings(),
            collection_name=chat_vector_store_collection_name,
            persist_directory=chat_vector_store_persist_directory
        )

        couplet_vector_store = Chroma.from_documents(
            documents=documents_by_couplet,
            embedding=OpenAIEmbeddings(),
            collection_name=couplet_vector_store_collection_name,
            persist_directory=couplet_vector_store_persist_directory
        )

    else:
        chat_vector_store = Chroma(persist_directory=chat_vector_store_persist_directory,
                                   embedding_function=OpenAIEmbeddings())
        couplet_vector_store = Chroma(persist_directory=couplet_vector_store_persist_directory,
                                      embedding_function=OpenAIEmbeddings())
    return chat_vector_store, couplet_vector_store


def split_string(s, length, splitter: str = "<br>") -> str:
    return splitter.join(s[i:i + length] for i in range(0, len(s), length))


async def create_vector_store_from_couplets(chats: Dict[str, DiscordChatDocument]):
    chat_vector_store, couplet_vector_store = await create_vector_store(chats=chats, run_embeddings=True)

    chat_output = await chat_vector_store.asimilarity_search("spinal central pattern generators", 4)
    couplet_output = await couplet_vector_store.asimilarity_search("spinal central pattern generators", 4)

    collection = couplet_vector_store._collection.get(include=["embeddings", "documents", "metadata"])
    # vector_stores = await get_or_create_student_message_vector_store()
    # embeddings = []

    # for student_name, vector_store in vector_stores.items():
    #     collection = vector_store._collection.get(include=["embeddings", "documents", "metadatas"])
    #     embeddings.extend(collection["embeddings"])
    #     labels.extend([split_string(document, 30) for document in collection["documents"]])
    labels = []
    for metadata in collection["metadatas"]:
        labels.append(f"{metadata['_student_initials']} - {metadata['source']}")
    visualize_clusters(embeddings=collection["embeddings"], labels=labels, n_clusters=5)


if __name__ == "__main__":
    database_name_in = "classbot_database"
    server_id = 1150736235430686720

    chats_out = asyncio.run(get_chats(database_name=database_name_in,
                                      query={"server_id": server_id}))
    chat_documents = {key: DiscordChatDocument.from_dict(chat_dict) for key, chat_dict in chats_out.items()}
    asyncio.run(create_vector_store_from_couplets(chats=chat_documents))
