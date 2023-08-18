import asyncio

from pydantic import BaseModel

from jonbot import get_logger
from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.conversation_memory import \
    ChatbotConversationMemoryBuilder, CONVERSATION_HISTORY_MAX_TOKENS
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import get_conversation_history
from jonbot.models.conversation_models import ChatRequest, ConversationHistory
from jonbot.models.database_request_response_models import ConversationHistoryRequest

logger = get_logger()


class MemoryCalculator(BaseModel):
    conversation_history_request: ConversationHistoryRequest
    conversation_history: ConversationHistory
    limit_messages: int = None
    memory: ChatbotConversationMemoryBuilder = ChatbotConversationMemoryBuilder.build()

    @classmethod
    async def from_conversation_history_request(cls, conversation_history_request: ConversationHistoryRequest,
                                                **kwargs):
        conversation_history = await get_conversation_history(conversation_history_request=conversation_history_request)
        return cls(conversation_history_request=conversation_history_request,
                   conversation_history=conversation_history,
                   **kwargs)

    @classmethod
    async def from_chat_request(cls, chat_request: ChatRequest, **kwargs):
        conversation_history_request = ConversationHistoryRequest.from_chat_request(chat_request=chat_request)
        return await cls.from_conversation_history_request(
            conversation_history_request=conversation_history_request,
            **kwargs)

    async def calculate(self):
        self.load_memory_from_history(conversation_history=self.conversation_history)
        return self.memory

    def load_memory_from_history(self,
                                 conversation_history=ConversationHistory,
                                 max_tokens=CONVERSATION_HISTORY_MAX_TOKENS,
                                 limit_messages=None):
        logger.info(f"Loading {len(conversation_history.get_all_messages())} messages into memory.")

        for chat_message in conversation_history.get_all_messages():
            if chat_message.speaker.type == "human":
                human_message = f"On {str(chat_message.timestamp)} the human {chat_message.speaker.name} said: {chat_message.message}"
                logger.trace(f"Adding human message: {human_message}")
                self.memory.chat_memory.add_user_message(human_message)
            elif chat_message.speaker.type == "bot":
                ai_message = f"On {str(chat_message.timestamp)}, the AI (you) {chat_message.speaker.name} said: {chat_message.message}"
                logger.trace(f"Adding AI message: {ai_message}")
                self.memory.chat_memory.add_ai_message(ai_message)
            memory_token_length = self.llm.get_num_tokens_from_messages(messages=self.chat_memory.messages)
            if memory_token_length > max_tokens:
                logger.info(f"Memory token length {memory_token_length} exceeds max tokens {max_tokens}. Pruning...")
                logger.info(f"Memory summary before pruning: {self.chat_memory.summary}\n---\n")
                self.prune()
                logger.info(f"Memory summary after pruning: {self.chat_memory.summary}")


async def calculate_memory(chat_request: ChatRequest):
    memory_calculator = await MemoryCalculator.from_chat_request(chat_request=chat_request)
    memory = await memory_calculator.calculate()
    return memory


if __name__ == "__main__":
    from jonbot.tests.load_save_sample_data import load_sample_chat_request

    chat_request = load_sample_chat_request()
    chat_request.config.limit_messages = None
    asyncio.run(calculate_memory(chat_request=chat_request))
