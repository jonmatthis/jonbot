from typing import Dict

from langchain import PromptTemplate
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)

from jonbot.backend.ai.chatbot.components.prompt.prompt_strings import (
    DEFAULT_RULES_FOR_LIVING,
    DEFAULT_CHATBOT_SYSTEM_PROMPT_TEMPLATE,
)
from jonbot.backend.data_layer.models.timestamp_model import Timestamp


class ChatbotPrompt(ChatPromptTemplate):
    @classmethod
    def build(
            cls,
            chat_history_placeholder_name: str,
            context_description_string: str,
            system_prompt_template: str = DEFAULT_CHATBOT_SYSTEM_PROMPT_TEMPLATE,
            extra_prompts: Dict[str, str] = None,
    ) -> ChatPromptTemplate:
        if extra_prompts is not None:
            extra_prompts_string = "\n".join(
                [f"Prompt Name {key}:\n {value}\n" for key, value in extra_prompts.items()]
            )
        else:
            extra_prompts_string = ""

        system_prompt = PromptTemplate(
            template=system_prompt_template,
            input_variables=[
                "timestamp",
                "rules_for_living",
                "context_description",
                "context_description",
                "extra_prompts_string",
                # "vectorstore_memory"
            ],
        )
        partial_system_prompt = system_prompt.partial(
            timestamp=str(Timestamp.now()),
            rules_for_living=DEFAULT_RULES_FOR_LIVING,
            context_description=context_description_string,
            extra_prompts_string=extra_prompts_string,
        )

        system_message_prompt = SystemMessagePromptTemplate(
            prompt=partial_system_prompt,
        )

        human_template = "{human_input}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return cls.from_messages(
            [
                system_message_prompt,
                MessagesPlaceholder(
                    variable_name=chat_history_placeholder_name,
                ),
                human_message_prompt,
            ]
        )


if __name__ == "__main__":
    print(ChatbotPrompt.build())
    f = 9
