import asyncio
import logging
from typing import AsyncGenerator, List, Any

from langchain import LLMChain
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.memory import CombinedMemory
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, validator

from jonbot.layer2_core_processes.ai_chatbot.components.callbacks.callbacks import AsyncQueueStuffingCallbackHandler
from jonbot.layer2_core_processes.ai_chatbot.components.memory.chatbot_memory_builder import ChatbotMemory
from jonbot.layer2_core_processes.ai_chatbot.components.prompt.prompt_builder import ChatbotPrompt
from jonbot.layer3_data_layer.database.get_or_create_mongo_database_manager import get_or_create_mongo_database_manager
from jonbot.models.conversation_models import ConversationContext, ConversationHistory, ChatRequest, ChatResponse

from jonbot import get_logger
logger = get_logger()


class AIChatBot(BaseModel):
    llm: BaseChatModel = None
    prompt: ChatPromptTemplate = None
    memory: CombinedMemory = None
    chain: LLMChain = None
    callbacks: List[Any] = [AsyncQueueStuffingCallbackHandler()]

    @classmethod
    async def build(cls,
                    conversation_context: ConversationContext = None,
                    conversation_history: ConversationHistory = None, ):
        logger.trace(f"Building AIChatBot")

        logger.trace(f"Building llm")
        llm = ChatOpenAI(
            streaming=True,
            callbacks=[],
            temperature=0.8,
            model_name="gpt-4")

        logger.trace(f"Building prompt")
        prompt = ChatbotPrompt.build(conversation_context=conversation_context)

        logger.trace(f"Building memory")
        memory = await ChatbotMemory.build(conversation_history=conversation_history)

        logger.trace(f"Building chain")
        chain = LLMChain(llm=llm,
                         prompt=prompt,
                         memory=memory,
                         verbose=True,
                         )
        logger.trace(f"Instantiating AIChatBot")
        instance = cls(llm=llm,
                       prompt=prompt,
                       memory=memory,
                       chain=chain)

        logger.trace(f"Adding callback handlers")
        for callback_handler in instance.callbacks:
            instance.llm.callbacks.append(callback_handler)

        logger.trace(f"Returning AIChatBot instance")
        return instance
    @validator('callbacks', pre=True, each_item=True)
    def validate_callback_handler(cls, v):
        if not isinstance(v, BaseCallbackHandler):
            raise ValueError(f"Expected BaseCallbackHandler, got {type(v)}")
        return v

    @classmethod
    async def from_chat_request(cls,
                                chat_request: ChatRequest):
        logger.trace(f"Building AIChatBot from chat_request: {chat_request}")
        mongo_database = await get_or_create_mongo_database_manager()
        logger.trace(f"Getting conversation_history from mongo_database: {mongo_database}")
        conversation_history = await mongo_database.get_conversation_history(
            context_route=chat_request.conversation_context.context_route)
        logger.trace(f"building AIChatBot with conversation_history: {conversation_history}")
        return await cls.build(conversation_context=chat_request.conversation_context,
                               conversation_history=conversation_history)

    def add_callback_handler(self,
                             handler: BaseCallbackHandler,
                             remove_existing: bool = False):
        logger.info(f"Adding callback handler: {handler}")
        if remove_existing:
            logger.info(f"Removing existing callback handlers ({self.llm.callbacks})")
            self.llm.callbacks = []
        self.llm.callbacks.append(handler)

    async def stream_chat_response_tokens(self, input_text: str) -> AsyncGenerator[str, None]:
        logger.info(f"Calling chain (as stream) with input_text: {input_text}")
        queue_stuffing_callback_handler = AsyncQueueStuffingCallbackHandler()
        self.add_callback_handler(handler=queue_stuffing_callback_handler)
        return await self.chain.acall(input={"human_input": input_text})


    async def get_chat_response(self,
                                chat_input_string: str) -> ChatResponse:
        logger.info(f"Calling chain with chat_input_string: {chat_input_string}")
        response_tokens = []
        async for token in self.chain.astream(input={"human_input": chat_input_string}):
            print(f"got token: {token}")
            response_tokens.append(token["text"])
        return ChatResponse.from_tokens(tokens=response_tokens)

    async def demo(self):
        print("Welcome to the ChatBot demo!")
        print("Type 'exit' to end the demo.\n")

        while True:
            input_text = input("Enter your input (or 'quit'): ")

            if input_text.strip().lower() == "quit":
                print("Ending the demo. Goodbye!")
                break

            chat_response = await self.get_chat_response(chat_input_string=input_text)

            print(f"Response: {chat_response.text}")


async def ai_chatbot_demo():
    from jonbot.system.configure_logging import TRACE
    logging.getLogger(__name__).setLevel(TRACE)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    chatbot = await AIChatBot.build()

    await chatbot.demo()


if __name__ == "__main__":
    asyncio.run(ai_chatbot_demo())
