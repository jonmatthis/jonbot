from langchain import PromptTemplate
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, \
    MessagesPlaceholder

from jonbot.layer2_processing.core_processing.ai.components.prompt.prompt_strings import DEFAULT_RULES_FOR_LIVING, \
    DEFAULT_CHATBOT_SYSTEM_PROMPT_TEMPLATE
from jonbot.models.conversation_context import ConversationContextDescription
from jonbot.models.timestamp_model import Timestamp


class ChatbotPrompt(ChatPromptTemplate):

    @classmethod
    def build(cls,
              chat_history_placeholder_name: str,
              conversation_context: ConversationContextDescription = None,
              system_prompt_template: str = DEFAULT_CHATBOT_SYSTEM_PROMPT_TEMPLATE,
              ) -> ChatPromptTemplate:
        system_prompt = PromptTemplate(template=system_prompt_template,
                                       input_variables=["timestamp",
                                                        "rules_for_living",
                                                        "context_route",
                                                        "context_description",
                                                        # "vectorstore_memory"
                                                        ],
                                       )
        partial_system_prompt = system_prompt.partial(timestamp=str(Timestamp.now()),
                                                      rules_for_living=DEFAULT_RULES_FOR_LIVING,
                                                      context_route=conversation_context.context_route.parent if conversation_context else '',
                                                      context_description=conversation_context.description if conversation_context else '', )

        system_message_prompt = SystemMessagePromptTemplate(
            prompt=partial_system_prompt,
        )

        human_template = "{human_input}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template
        )

        return cls.from_messages(
            [system_message_prompt,
             MessagesPlaceholder(variable_name=chat_history_placeholder_name, ),
             human_message_prompt]
        )


if __name__ == "__main__":
    print(ChatbotPrompt.build())
    f = 9
