from langchain import OpenAI
from langchain.memory import ConversationSummaryBufferMemory

from jonbot.models.conversation_models import ConversationHistory

CONVERSATION_HISTORY_MAX_TOKENS = 1000

import logging

logger = logging.getLogger(__name__)


class ChatbotConversationMemoryBuilder(ConversationSummaryBufferMemory):
    @classmethod
    def build(cls, conversation_history: ConversationHistory = None):
        instance = cls(memory_key="chat_memory",
                       input_key="human_input",
                       llm=OpenAI(temperature=0),
                       max_token_limit=CONVERSATION_HISTORY_MAX_TOKENS)

        if conversation_history is not None:
            instance.load_memory_from_history(conversation_history=conversation_history)

        return instance

    def load_memory_from_history(self,
                                 conversation_history=ConversationHistory,
                                 max_tokens=CONVERSATION_HISTORY_MAX_TOKENS):
        logger.info(f"Loading {len(conversation_history.get_all_messages())} messages into memory.")

        for chat_message in conversation_history.get_all_messages():
            if chat_message.speaker.type == "human":
                self.chat_memory.add_user_message(
                    f"On {str(chat_message.timestamp)} the human {chat_message.speaker.name} said: {chat_message.message}")
            elif chat_message.speaker.type == "bot":
                self.chat_memory.add_ai_message(
                    f"On {str(chat_message.timestamp)}, the AI (you) {chat_message.speaker.name} said: {chat_message.message}")
            if self.llm.get_num_tokens_from_messages(
                    messages=self.chat_memory.messages) > max_tokens:
                self.prune()
                break
