from langchain import OpenAI, PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory

from jonbot.models.conversation_models import ConversationHistory

CONVERSATION_HISTORY_MAX_TOKENS = 1000

from jonbot import get_logger

logger = get_logger()


CUSTOM_SUMMARIZER_TEMPLATE = """Progressively summarize the lines of conversation provided, adding onto the previous summary returning a new summary.

---------
THIS IS AN **EXAMPLE** OF A WAY TO SUMMARIZE A **DIFFERENT** CONVERSATION. THIS IS NOT THE CONVERSATION YOU ARE SUMMARIZING.
EXAMPLE
Current summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good.

New lines of conversation:
(Example)Human: Why do you think artificial intelligence is a force for good?
(Example)AI: Because artificial intelligence will help humans reach their full potential.

New summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.
END OF EXAMPLE

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:"""
CUSTOM_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["summary", "new_lines"], template=CUSTOM_SUMMARIZER_TEMPLATE
)

class ChatbotConversationMemoryBuilder(ConversationSummaryBufferMemory):
    @classmethod
    def build(cls, conversation_history: ConversationHistory = None):
        instance = cls(memory_key="chat_memory",
                       input_key="human_input",
                       llm=OpenAI(temperature=0),
                       return_messages=True,
                       max_token_limit=CONVERSATION_HISTORY_MAX_TOKENS, )
        instance.prompt = CUSTOM_SUMMARY_PROMPT
        if conversation_history is not None:
            instance.load_memory_from_history(conversation_history=conversation_history)

        return instance

    def load_memory_from_history(self,
                                 conversation_history=ConversationHistory,
                                 max_tokens=CONVERSATION_HISTORY_MAX_TOKENS):
        logger.info(f"Loading {len(conversation_history.get_all_messages())} messages into memory.")

        for chat_message in conversation_history.get_all_messages():
            if chat_message.speaker.type == "human":
                human_message = f"On {str(chat_message.timestamp)} the human {chat_message.speaker.name} said: {chat_message.message}"
                logger.trace(f"Adding human message: {human_message}")
                self.chat_memory.add_user_message(human_message)
            elif chat_message.speaker.type == "bot":
                ai_message = f"On {str(chat_message.timestamp)}, the AI (you) {chat_message.speaker.name} said: {chat_message.message}"
                logger.trace(f"Adding AI message: {ai_message}")
                self.chat_memory.add_ai_message(ai_message)
            if self.llm.get_num_tokens_from_messages(
                    messages=self.chat_memory.messages) > max_tokens:
                self.prune()

