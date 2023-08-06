import asyncio
import logging
from typing import Any, OrderedDict

from dotenv import load_dotenv
from langchain import LLMChain, OpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import CombinedMemory, VectorStoreRetrieverMemory, ConversationSummaryBufferMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.vectorstores import Chroma
from pydantic import BaseModel

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot_prompts import CHATBOT_SYSTEM_PROMPT_TEMPLATE, RULES_FOR_LIVING
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ChatInput, ConversationHistory
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp
from jonbot.layer3_data_layer.system.filenames_and_paths import get_chroma_vector_store_path

load_dotenv()

from typing import Callable


class CustomStreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, token_handler: Callable[[str], None] = None):
        self.token_handler = token_handler

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.token_handler(token)



class AIChatBot(BaseModel):
    llm: ChatOpenAI = ChatOpenAI(
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
        temperature=0.8,
        model_name="gpt-4")
    chat_history: str = []
    prompt: Any = None
    memory: Any = None
    chain: Any = None
    context_route: str = "The human is talking to your through an unknown interface."
    context_description= "You are having a conversation with a human."


    async def create_chatbot(self):
        if self.prompt is None:
            self.prompt = self._create_prompt(system_prompt_template=CHATBOT_SYSTEM_PROMPT_TEMPLATE)
        if self.memory is None:
            self.memory = await self._configure_memory()
        if self.chain is None:
            self.chain = self._create_llm_chain()
        return self

    def add_callback(self, callback: BaseCallbackHandler):
        self.llm.callbacks.append(callback)

    async def _configure_memory(self):
        conversation_memory = self._configure_conversation_memory()
        vectorstore_memory = await self._configure_vectorstore_memory()
        combined_memory = CombinedMemory(memories=[conversation_memory,
                                                   vectorstore_memory])
        return combined_memory

    async def _configure_vectorstore_memory(self, ):
        chroma_vector_store = await self._create_vector_store()

        retriever = chroma_vector_store.as_retriever(search_kwargs=dict(k=4))

        return VectorStoreRetrieverMemory(retriever=retriever,
                                          memory_key="vectorstore_memory",
                                          input_key="human_input",
                                          )

    @staticmethod
    def _configure_conversation_memory():
        return ConversationSummaryBufferMemory(memory_key="chat_memory",
                                               input_key="human_input",
                                               llm=OpenAI(temperature=0),
                                               max_token_limit=1000)

    def _create_llm_chain(self):
        return LLMChain(llm=self.llm,
                        prompt=self.prompt,
                        memory=self.memory,
                        verbose=True,
                        )

    def _create_prompt(self, system_prompt_template: str):
        system_message_prompt = SystemMessagePromptTemplate(
            template=system_prompt_template,
            input_variables=["timestamp",
                             "rules_for_living",
                             "context_route",
                             "context_description",
                             "chat_memory",
                             "vectorstore_memory"
                             ]
        )
        system_message_prompt.prompt.partial(timestamp = Timestamp(),
                                             rules_for_living = RULES_FOR_LIVING,
                                             context_route = self.context_route,
                                             context_description = self.context_description,)


        human_template = "{human_input}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template
        )

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        return chat_prompt

    async def async_process_human_input_text(self, input_text: str):
        print(f"Input: {input_text}")
        print("Streaming response...\n")
        ai_response = await self.chain.arun(human_input=input_text)
        return ai_response

    async def async_process_human_input_text_streaming(self, input_text: str):
        print(f"Input: {input_text}")
        print("Streaming response...\n")

        async def token_handler(token: str):
            yield token

        callback_handler = CustomStreamingCallbackHandler(token_handler=token_handler)
        self.add_callback(callback_handler)
        await self.chain.arun(human_input=input_text)
        return token_handler

    def load_memory_from_history(self, conversation_history=ConversationHistory):
        for entry in conversation_history.get_all_messages():
            if isinstance(entry, ChatInput):
                self.memory.memories[0].chat_memory.add_user_message(entry.message)
            elif isinstance(entry, ChatResponse):
                self.memory.memories[0].chat_memory.add_ai_message(entry.message)

    async def _create_vector_store(self, collection_name: str = "test_collection"):
        chroma_vector_store = Chroma(
            embedding_function=OpenAIEmbeddings(),
            collection_name=collection_name,
            persist_directory=str(get_chroma_vector_store_path()),
        )
        return chroma_vector_store

    async def get_chat_response(self, chat_input: ChatInput) -> ChatResponse:
        response = await self.async_process_human_input_text(chat_input.message)
        return ChatResponse(message=response, )

    async def demo(self):
        print("Welcome to the ChatBot demo!")
        print("Type 'exit' to end the demo.\n")

        while True:
            input_text = input("Enter your input (or 'quit'): ")

            if input_text.strip().lower() == "quit":
                print("Ending the demo. Goodbye!")
                break

            chat_response = await self.get_chat_response(chat_input=ChatInput(message=input_text))

            print(f"Response: {chat_response.message}")


async def ai_chatbot_demo():
    logging.getLogger(__name__).setLevel(logging.WARNING)
    chatbot = await AIChatBot().create_chatbot()
    await chatbot.demo()


if __name__ == "__main__":
    asyncio.run(ai_chatbot_demo())
