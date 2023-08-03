import asyncio
from typing import Any

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

from jonbot.layer2_core_processes.processing_sublayer.ai.chatbot.chatbot_prompts import CHATBOT_SYSTEM_PROMPT_TEMPLATE
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ChatInput
from jonbot.layer3_data_layer.system.filenames_and_paths import get_chroma_vector_store_path

load_dotenv()


class Chatbot(BaseModel):
    llm: ChatOpenAI = ChatOpenAI(
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
        temperature=0.8,
        model_name="gpt-4")
    prompt: Any = None
    memory: Any = None
    chain: Any = None

    async def create_chatbot(self):
        if self.prompt is None:
            self.prompt = self._create_prompt(prompt_template=CHATBOT_SYSTEM_PROMPT_TEMPLATE)
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

        retriever = chroma_vector_store.as_retriever(search_kwargs=dict(k=1))

        return VectorStoreRetrieverMemory(retriever=retriever,
                                          memory_key="vectorstore_memory",
                                          input_key="human_input", )

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

    def _create_prompt(self, prompt_template: str):
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            prompt_template
        )

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

    async def load_memory_from_thread(self, thread, bot_name: str):
        async for message in thread.history(limit=None, oldest_first=True):
            if message.content == "":
                continue
            if str(message.author) == bot_name:
                self.memory.memories[0].chat_memory.add_ai_message(message.content)
            else:
                self.memory.memories[0].chat_memory.add_user_message(message.content)

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


if __name__ == "__main__":
    async def main():
        chatbot = await Chatbot().create_chatbot()
        await chatbot.demo()


    asyncio.run(main())
