# from typing import Union
#
# from langchain.schema import HumanMessage, AIMessage
# from pydantic import BaseModel
#
# from jonbot import get_logger
# from jonbot.layer2_processing.backend_database_operator.backend_database_operator import \
#     BackendDatabaseOperations
# from jonbot.layer2_processing.core.ai.chatbot_llm_chain.components.memory.conversation_memory.conversation_memory import \
#     ChatbotConversationMemory
# from jonbot.models.calculate_memory_request import CalculateMemoryRequest
# from jonbot.models.context_memory_document import ContextMemoryDocument
# from jonbot.models.conversation_models import MessageHistory, ChatMessage
# from jonbot.models.database_request_response_models import MessageHistoryRequest, ContextMemoryDocumentRequest
# from jonbot.models.memory_config import CONVERSATION_HISTORY_MAX_TOKENS
#
# logger = get_logger()
#
#
# class MemoryDataCalculator(BaseModel):
#     calculate_memory_request: CalculateMemoryRequest
#     current_context_memory: ContextMemoryDocument = None
#     message_history: MessageHistory
#     max_tokens = CONVERSATION_HISTORY_MAX_TOKENS
#     database_operations: BackendDatabaseOperations
#
#     memory: ChatbotConversationMemory = ChatbotConversationMemory()
#
#     @classmethod
#     async def from_calculate_memory_request(cls,
#                                             calculate_memory_request: CalculateMemoryRequest,
#                                             database_operations: BackendDatabaseOperations, ):
#
#         current_context_memory = await cls._get_current_context_memory(calculate_memory_request, database_operations)
#
#         if current_context_memory is None:
#             logger.warning(f"Context memory not found for request: {calculate_memory_request.context_route.dict()}")
#             return
#
#         message_history = await cls._get_message_history(calculate_memory_request, database_operations)
#
#         if message_history is None:
#             logger.warning(f"Message history not found for request: {calculate_memory_request.context_route.dict()}")
#             return
#
#         logger.info(f"Loaded {len(message_history.get_all_messages())} messages from history for context route: "
#                     f"{calculate_memory_request.context_route.friendly_path}")
#
#         return cls(calculate_memory_request=calculate_memory_request,
#                    current_context_memory=current_context_memory,
#                    message_history=message_history,
#                    limit_messages=calculate_memory_request.limit_messages,
#                    database_operations=database_operations)
#
#     @classmethod
#     async def _get_message_history(cls, calculate_memory_request, database_operations):
#         message_history = await database_operations.get_message_history_document(
#             request=MessageHistoryRequest(context_route=calculate_memory_request.context_route,
#                                           database_name=calculate_memory_request.database_name,
#                                           limit_messages=calculate_memory_request.limit_messages))
#         return message_history
#
#     @classmethod
#     async def _get_current_context_memory(cls, calculate_memory_request, database_operations):
#         current_context_memory = await database_operations.get_context_memory_document(
#             ContextMemoryDocumentRequest.build_get_request(
#                 context_route=calculate_memory_request.context_route,
#                 database_name=calculate_memory_request.database_name))
#         return current_context_memory
#
#     async def calculate(self,
#                         upsert: bool = True,
#                         overwrite: bool = False) -> ContextMemoryDocument:
#
#         self.calculate_memory_from_history(message_history=self.message_history,
#                                            limit_messages=self.calculate_memory_request.limit_messages,
#                                            overwrite=overwrite)
#
#         context_memory_document = ContextMemoryDocument(
#             context_route=self.calculate_memory_request.context_route,
#             message_buffer=[message.dict() for message in self.memory.buffer],
#             summary=self.memory.moving_summary_buffer,
#             summary_prompt=self.memory.prompt,
#             token_count=self.memory.token_count,
#         )
#
#         if upsert:
#             await self.database_operations.upsert_context_memory(
#                 ContextMemoryDocumentRequest(data=context_memory_document,
#                                              database_name=self.calculate_memory_request.database_name,
#                                              query=self.calculate_memory_request.context_route.as_query))
#
#         return context_memory_document
#
#     def calculate_memory_from_history(self,
#                                       message_history: MessageHistory,
#                                       limit_messages: int = None,
#                                       overwrite: bool = False):
#         logger.info(
#             f"Calculating memory from history for context route: {self.calculate_memory_request.context_route.friendly_path} using {len(message_history.get_all_messages())} messages...")
#
#         previously_calculated_uuids = []
#         if self.current_context_memory is not None:
#             previously_calculated_uuids = self.current_context_memory.message_uuids
#
#         message_count = -1
#         for chat_message in message_history.get_all_messages():
#             if chat_message.uuid in previously_calculated_uuids and not overwrite:
#                 logger.trace(
#                     f"Skipping message with uuid {chat_message.uuid} because it has already been incorporated into context memory.")
#                 continue
#
#             message_count += 1
#             if limit_messages is not None:
#                 logger.trace(f"Limiting messages to {limit_messages} - currently at {message_count}")
#                 if message_count > limit_messages:
#                     logger.trace(f"Reached limit of {limit_messages} messages. Breaking...")
#                     break
#
#             typed_message = self._create_typed_message(chat_message)
#             logger.debug(f"Adding message to memory: {typed_message.dict()}")
#             self.memory.chat_memory.add_message(typed_message)
#
#             memory_token_length = self.memory.llm.get_num_tokens_from_messages(
#                 messages=self.memory.chat_memory.messages)
#             if memory_token_length > self.max_tokens:
#                 logger.info(
#                     f"Memory token length {memory_token_length} exceeds max tokens {self.max_tokens}. Pruning...")
#                 logger.info(f"Memory summary before pruning: {self.memory.moving_summary_buffer}\n---\n")
#                 self.memory.prune()
#                 logger.info(f"Memory summary after pruning: {self.memory.moving_summary_buffer}")
#
#         self.memory.moving_summary_buffer = self.memory.predict_new_summary(messages=self.memory.chat_memory.messages,
#                                                                             existing_summary=self.memory.moving_summary_buffer)
#
#     def _create_typed_message(self, chat_message: ChatMessage) -> Union[HumanMessage, AIMessage]:
#         if chat_message.speaker.type == "human":
#             human_message = self._create_human_message_from_chat_message(chat_message)
#             logger.trace(f"Created human message: {human_message}")
#             return human_message
#
#         elif chat_message.speaker.type == "bot":
#             ai_message = self._create_ai_message_from_chat_message(chat_message)
#             logger.trace(f"Created AI message: {ai_message}")
#             self.memory.chat_memory.add_message(ai_message)
#             return ai_message
#
#     def _create_ai_message_from_chat_message(self, chat_message):
#         ai_message = AIMessage(
#             content=f"{chat_message.content} - "
#                     f"["
#                     f"metadata - "
#                     f"'username':{chat_message.speaker.name},"
#                     f"'local_time': {chat_message.timestamp.human_readable_local},"
#                     f"'notes': (this is you)"
#                     f"]",
#             additional_kwargs={**chat_message.dict(),
#                                "type": "ai"})
#         return ai_message
#
#     def _create_human_message_from_chat_message(self, chat_message):
#         human_message = HumanMessage(
#             content=f"{chat_message.content} "
#                     f"["
#                     f"metadata - "
#                     f"'username':{chat_message.speaker.name},"
#                     f"'local_time': {chat_message.timestamp.human_readable_local}"
#                     f"]",
#             additional_kwargs={**chat_message.dict(),
#                                "type": "human"})
#         logger.trace(f"Adding human message: {human_message}")
#         return human_message
