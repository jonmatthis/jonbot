from abc import ABC, abstractmethod
from typing import Type

from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from jonbot.backend.data_layer.analysis.document_from_channel import SIMPLE_CONVERSATION_SUMMARIZER_PROMPT_TEMPLATE, \
    TOPIC_EXTRACTOR_PROMPT_TEMPLATE
from jonbot.backend.data_layer.analysis.summarize_chats.summarize_chats import GLOBAL_TOPIC_TREE_PROMPT, \
    CONTEXT_PAPER_DOCUMENT_GENERATOR_PROMPT


class BaseChain(ABC):
    def __init__(self, temperature: float, model_name: str, max_tokens: int = None):
        self.llm = ChatOpenAI(temperature=temperature, model_name=model_name, max_tokens=max_tokens)

    @abstractmethod
    def get_template(self) -> Type[ChatPromptTemplate]:
        pass

    def create_chain(self):
        prompt = self.get_template()
        chain = prompt | self.llm
        return chain


class SimpleSummaryChain(BaseChain):
    def get_template(self):
        return ChatPromptTemplate.from_template(SIMPLE_CONVERSATION_SUMMARIZER_PROMPT_TEMPLATE)


class TopicExtractorChain(BaseChain):
    def get_template(self):
        return ChatPromptTemplate.from_template(TOPIC_EXTRACTOR_PROMPT_TEMPLATE)


class GlobalTopicTreeChain(BaseChain):
    def get_template(self):
        return ChatPromptTemplate.from_template(GLOBAL_TOPIC_TREE_PROMPT)


class ContextPaperDocumentGeneratorChain(BaseChain):
    def get_template(self):
        return ChatPromptTemplate.from_template(CONTEXT_PAPER_DOCUMENT_GENERATOR_PROMPT)
