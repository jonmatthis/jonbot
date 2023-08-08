import asyncio
import logging
from typing import Any
from typing import Callable

from dotenv import load_dotenv
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains.base import Chain
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import CombinedMemory, VectorStoreRetrieverMemory, ConversationSummaryBufferMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.vectorstores import Chroma
from pydantic import BaseModel

from jonbot.layer2_core_processes.ai_chatbot.ai_chatbot_prompts import CHATBOT_SYSTEM_PROMPT_TEMPLATE, RULES_FOR_LIVING
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ChatInput, ConversationHistory, \
    ChatRequest
from jonbot.layer3_data_layer.data_models.timestamp_model import Timestamp
from jonbot.layer3_data_layer.system.filenames_and_paths import get_chroma_vector_store_path

CONVERSATION_HISTORY_MAX_TOKENS = 1000


load_dotenv()
logger = logging.getLogger(__name__)


class CustomStreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, token_handler: Callable[[str], None] = None):
        self.token_handler = token_handler

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.token_handler(token)


class AIChatBot(BaseModel):
    llm: BaseChatModel = None
    conversation_history: ConversationHistory = None
    prompt: ChatPromptTemplate = None
    memory: CombinedMemory = None
    chain: Chain = None
    context_route: str = "The human is talking to your through an unknown interface."
    context_description: str = "You are having a conversation with a human."

    @classmethod
    async def from_chat_request(cls,
                                chat_request: ChatRequest,
                                conversation_history: ConversationHistory = None,):

        cls.context_route = chat_request.conversational_context.context_route
        cls.context_description = chat_request.conversational_context.context_description

        cls.llm = ChatOpenAI(
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            temperature=0.8,
            model_name="gpt-4") if cls.llm is None else cls.llm

        cls.prompt = cls._create_prompt(
            system_prompt_template=CHATBOT_SYSTEM_PROMPT_TEMPLATE) if cls.prompt is None else cls.prompt

        cls.memory = await cls._configure_memory() if cls.memory is None else cls.memory

        if conversation_history is not None:
            cls.load_memory_from_history(conversation_history=conversation_history)

        cls.chain = cls._create_llm_chain()

        return cls

    def add_callback(self, callback: BaseCallbackHandler):
        self.llm.callbacks.append(callback)

    async def _configure_memory(self):

        combined_memory = CombinedMemory(memories=[self._configure_conversation_memory(),
                                                   await self._configure_vectorstore_memory()])

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
                                               max_token_limit=CONVERSATION_HISTORY_MAX_TOKENS)

    def _create_llm_chain(self):
        return LLMChain(llm=self.llm,
                        prompt=self.prompt,
                        memory=self.memory,
                        verbose=True,
                        )

    def _create_prompt(self, system_prompt_template: str):
        system_prompt = PromptTemplate(template=system_prompt_template,
                                       input_variables=["timestamp",
                                                        "rules_for_living",
                                                        "context_route",
                                                        "context_description",
                                                        "chat_memory",
                                                        "vectorstore_memory"
                                                        ],
                                       )
        partial_system_prompt = system_prompt.partial(timestamp=str(Timestamp.now()),
                                                      rules_for_living=RULES_FOR_LIVING,
                                                      context_route=self.context_route,
                                                      context_description=self.context_description, )

        system_message_prompt = SystemMessagePromptTemplate(
            prompt=partial_system_prompt,
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
        logger.info(f"Input: {input_text}")
        logger.info("Streaming response...\n")
        ai_response = await self.chain.acall(inputs={"human_input": input_text})

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

    def load_memory_from_history(self,
                                 conversation_history=ConversationHistory,
                                 max_tokens=CONVERSATION_HISTORY_MAX_TOKENS):

        logger.info(f"Loading {len(conversation_history.get_all_messages())} messages into memory.")

        for chat_message in conversation_history.get_all_messages():
            if chat_message.speaker.type == "human":
                self.memory.memories[0].chat_memory.add_user_message(
                    f"On {str(chat_message.timestamp)} the human {chat_message.speaker.name} said: {chat_message.message}")
            elif chat_message.speaker.type == "bot":
                self.memory.memories[0].chat_memory.add_ai_message(
                    f"On {str(chat_message.timestamp)}, the AI (you) {chat_message.speaker.name} said: {chat_message.message}")
            if self.llm.get_num_tokens_from_messages(
                    messages=self.memory.memories[0].chat_memory.messages) > max_tokens:
                self.memory.memories[0].prune()
                break

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
    chatbot = AIChatBot()
    await chatbot.intialize()
    await chatbot.demo()


if __name__ == "__main__":
    asyncio.run(ai_chatbot_demo())
