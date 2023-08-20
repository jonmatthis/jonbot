
from typing import List, Union, Any, Dict

from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import HumanMessage, AIMessage

from jonbot import get_logger
from jonbot.models.memory_config import ChatbotConversationMemoryConfig

logger = get_logger()


class ChatbotConversationMemory(ConversationSummaryBufferMemory):
    def __init__(self, config: ChatbotConversationMemoryConfig = None):
        if config is None:
            config = ChatbotConversationMemoryConfig()

        super().__init__(
            memory_key=config.memory_key,
            input_key=config.input_key,
            llm=config.llm,
            return_messages=config.return_messages,
            max_token_limit=config.max_token_limit,
        )

        self.prompt = config.summary_prompt

    @property
    def token_count(self) -> int:
        tokens_in_messages = self.llm.get_num_tokens_from_messages(self.buffer)
        tokens_in_summary = self.llm.get_num_tokens(self.moving_summary_buffer)
        return tokens_in_messages + tokens_in_summary



    def load_messages_from_message_buffer(self, buffer:List[Dict[str, Any]]) -> List[Union[HumanMessage, AIMessage]]:
        messages = []
        try:
            for message_dict in buffer:
                if message_dict["additional_kwargs"]["type"] == "human":
                    messages.append(HumanMessage(**message_dict))
                elif message_dict["additional_kwargs"]["type"] == "ai":
                    messages.append(AIMessage(**message_dict))
            self.chat_memory.messages =  messages
        except Exception as e:
            logger.exception(e)
            raise
