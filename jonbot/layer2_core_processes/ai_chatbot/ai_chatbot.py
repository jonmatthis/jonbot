import asyncio
import logging
from typing import Any
from typing import Callable

from dotenv import load_dotenv
from langchain import LLMChain
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains.base import Chain
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.memory import CombinedMemory
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel

from jonbot.layer2_core_processes.ai_chatbot.components.memory.chatbot_memory_builder import ChatbotMemoryBuilder
from jonbot.layer2_core_processes.ai_chatbot.components.prompt.prompt_builder import ChatbotPromptBuilder
from jonbot.layer3_data_layer.data_models.conversation_models import ChatResponse, ConversationHistory, \
    ConversationContext

load_dotenv()
logger = logging.getLogger(__name__)


class CustomStreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, token_handler: Callable[[str], None] = None):
        self.token_handler = token_handler

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.token_handler(token)


class AIChatBotBuilder(BaseModel):
    llm: BaseChatModel = None
    prompt: ChatPromptTemplate = None
    memory: CombinedMemory = None
    chain: Chain = None

    @classmethod
    async def build(cls,
                    conversation_context: ConversationContext = None,
                    conversation_history: ConversationHistory = None, ):
        llm = ChatOpenAI(
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            temperature=0.8,
            model_name="gpt-4")

        prompt = ChatbotPromptBuilder.build(conversation_context=conversation_context)

        memory = await ChatbotMemoryBuilder.build(conversation_history=conversation_history)

        chain = LLMChain(llm=llm,
                         prompt=prompt,
                         memory=memory,
                         verbose=True,
                         )

        return cls(llm=llm,
                   prompt=prompt,
                   memory=memory,
                   chain=chain)

    def add_callback_handler(self, handler: BaseCallbackHandler):
        logger.info(f"Adding callback handler: {handler}")
        self.llm.callbacks.append(handler)

    async def stream_chat_response_tokens(self, input_text: str):
        logger.info(f"Calling chain (as stream) with input_text: {input_text}")
        async for token in self.chain.astream(input={"human_input": input_text}):
            yield token["text"]

    async def get_chat_response(self,
                                chat_input_string: str) -> ChatResponse:
        logger.info(f"Calling chain with chat_input_string: {chat_input_string}")
        response = await self.chain.acall(inputs={"human_input": chat_input_string})
        return ChatResponse(text=response["text"])

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
    logging.getLogger(__name__).setLevel(logging.WARNING)
    chatbot = await AIChatBotBuilder.build()
    await chatbot.demo()


if __name__ == "__main__":
    asyncio.run(ai_chatbot_demo())
