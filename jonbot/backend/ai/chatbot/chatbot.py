import inspect
import traceback
from typing import AsyncIterable, Union

from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableMap, RunnableSequence

from jonbot.backend.ai.chatbot.components.memory.conversation_memory.conversation_memory import (
    ChatbotConversationMemory,
)
from jonbot.backend.ai.chatbot.components.prompt.prompt_builder import (
    ChatbotPrompt,
)
from jonbot.backend.backend_database_operator.backend_database_operator import (
    BackendDatabaseOperations,
)
from jonbot.backend.data_layer.models.context_route import ContextRoute
from jonbot.backend.data_layer.models.conversation_context import ConversationContextDescription
from jonbot.backend.data_layer.models.conversation_models import ChatRequestConfig, ChatRequest
from jonbot.frontends.discord_bot.handlers.discord_message_responder import (
    STOP_STREAMING_TOKEN,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

# langchain.debug = True

logger = get_jonbot_logger()


class Chatbot:
    memory: ChatbotConversationMemory
    model: BaseChatModel
    prompt: ChatPromptTemplate
    chain: RunnableSequence

    def __init__(
            self,
            human_user_id: Union[str, int],
            context_route: ContextRoute,
            conversation_context_description: ConversationContextDescription,
            database_name: str,
            database_operations: BackendDatabaseOperations,
            config: ChatRequestConfig,
            chat_history_placeholder_name: str = "chat_history",
    ):
        self.frontend_bot_nickname = f"{database_name.split('_')[0]}"
        self.chat_history_placeholder_name = chat_history_placeholder_name
        self.context_route = context_route
        self.conversation_context_description = conversation_context_description
        self.human_user_id = human_user_id
        self.config = config
        self.tags = [self.frontend_bot_nickname,
                     f"user: {self.human_user_id}",
                     *[f"{key} : {value}" for key, value in self.context_route.as_flat_dict.items()],
                     ]
        self.memory = ChatbotConversationMemory(
            database_operations=database_operations,
            database_name=database_name,
            context_route=self.context_route,
        )

    @classmethod
    async def from_context_route(
            cls,
            human_user_id: Union[str, int],
            context_route: ContextRoute,
            conversation_context_description: ConversationContextDescription,
            database_name: str,
            database_operations: BackendDatabaseOperations,
            chat_request_config: ChatRequestConfig = None,
    ):
        instance = cls(
            human_user_id=human_user_id,
            context_route=context_route,
            database_name=database_name,
            conversation_context_description=conversation_context_description,
            database_operations=database_operations,
            config=chat_request_config,

        )
        await instance.apply_config_and_build_chain(config=chat_request_config)

        return instance

    @classmethod
    def from_chat_request(cls,
                          chat_request: ChatRequest,
                          database_operations: BackendDatabaseOperations):
        return cls.from_context_route(
            human_user_id=chat_request.user_id,
            context_route=chat_request.context_route,
            conversation_context_description=chat_request.conversation_context_description,
            database_name=chat_request.database_name,
            database_operations=database_operations,
            chat_request_config=chat_request.config,
        )

    def _build_chain(self) -> RunnableSequence:
        return (
                RunnableMap(
                    {
                        "human_input": lambda x: x["human_input"],
                        "memory": self.memory.load_memory_variables,
                    }
                )
                | {
                    "human_input": lambda x: x["human_input"],
                    "chat_history": lambda x: x["memory"]["chat_memory"],
                }
                | self.prompt
                | self.model
        )

    async def apply_config_and_build_chain(self, config: ChatRequestConfig):
        logger.debug(f"Applying config: {config} to chatbot chain...")
        if self.memory is None:
            logger.error(f"Memory not configured!")
            raise Exception("Memory not configured!")

        self.model = ChatOpenAI(
            temperature=config.temperature,
            model_name=config.model_name,
            verbose=True,
        )
        self.prompt = ChatbotPrompt.build(
            chat_history_placeholder_name=self.chat_history_placeholder_name,
            context_description_string=self.conversation_context_description.text,
            config_prompts=config.config_prompts,
        )

        await self.memory.set_memory_messages(config.memory_messages)

        self.chain = self._build_chain()

    async def execute(
            self,
            message_string: str,
            message_id: int,
            reply_message_id: int,
    ) -> AsyncIterable[str]:

        inputs = {"human_input": message_string,
                  "message_id": message_id,
                  }
        response_message = ""
        try:

            async for token in self.chain.astream(inputs, {"tags": self.tags}):
                logger.trace(f"Yielding token: {repr(token.content)}")
                response_message += token.content
                yield token.content
            yield STOP_STREAMING_TOKEN

            logger.debug(f"Successfully executed chain! - Saving context to memory...")

            logger.trace(f"Response message: {response_message}")
            await self.memory.update(
                inputs=inputs,
                outputs={"output": f"{response_message}",
                         "message_id": reply_message_id},
            )

        except Exception as e:
            logger.exception(e)

            # Extracting traceback details
            tb = traceback.extract_tb(e.__traceback__)
            file_name, line_number, func_name, text = tb[-1]  # Getting details of the last (most recent) call

            class_name = self.__class__.__name__
            current_frame = inspect.currentframe()
            yield f"ERROR (from {class_name}.{func_name} at line {line_number}) - \n >  {str(e)}\n\n"
            yield STOP_STREAMING_TOKEN
            raise

    def configure(self, config):
        pass

# async def demo():
#     from jonbot.tests.load_save_sample_data import load_sample_message_history
#
#     conversation_history = await load_sample_message_history()
#     llm_chain = ChatbotLLMChain(conversation_history=conversation_history)
#     async for token in llm_chain.chain.astream(
#             {"human_input": "Hello, how are you?"}
#     ):  # Use 'async for' here
#         print(token.content)
#     f = 9
#
#
# if __name__ == "__main__":
#     asyncio.run(demo())
