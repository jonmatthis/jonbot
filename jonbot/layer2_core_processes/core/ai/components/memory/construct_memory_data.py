import asyncio

from pydantic import BaseModel

from jonbot.layer2_core_processes.core.ai.components.memory.sub_memory_components.conversation_memory import \
    ChatbotConversationMemoryBuilder
from jonbot.layer2_core_processes.entrypoint_functions.database_actions import get_conversation_history
from jonbot.models.conversation_models import ChatRequest, ConversationHistory
from jonbot.models.database_request_response_models import ConversationHistoryRequest


class MemoryCalculator(BaseModel):
    conversation_history_request: ConversationHistoryRequest
    conversation_history: ConversationHistory
    memory: ChatbotConversationMemoryBuilder = None

    @classmethod
    async def from_conversation_history_request(cls, conversation_history_request: ConversationHistoryRequest):
        conversation_history = await get_conversation_history(conversation_history_request=conversation_history_request)
        return cls(conversation_history_request=conversation_history_request,
                   conversation_history=conversation_history)

    @classmethod
    async def from_chat_request(cls, chat_request: ChatRequest):
        conversation_history_request = ConversationHistoryRequest.from_chat_request(chat_request=chat_request)
        return await cls.from_conversation_history_request(conversation_history_request=conversation_history_request)

    async def calculate(self):
        self.memory = ChatbotConversationMemoryBuilder.build(conversation_history=self.conversation_history)
        return self.memory


async def calculate_memory(chat_request: ChatRequest):
    memory_calculator = await MemoryCalculator.from_chat_request(chat_request=chat_request)
    memory = await memory_calculator.calculate()
    return memory


if __name__ == "__main__":
    from jonbot.tests.load_save_sample_data import load_sample_chat_request

    chat_request = load_sample_chat_request()
    asyncio.run(calculate_memory(chat_request=chat_request))
