
from typing import List, Union, Any, Dict

from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel

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

class ContextMemoryHandler(BaseModel):
    Help
    me
    refactor
    these
    classes
    so
    that
    I
    can
    make
    it
    cleaner and more
    modular

    Here
    are
    some
    POTENTIAL
    changes
    that
    MIGHT
    improve
    it? I
    really
    don
    't know though, please et me know what you think!

    - remove
    database and memory
    update
    stuff
    from the LLMChain
    class - maybe move it to the  ChatbotConversationMemory

    - Refactor
    the
    MemoryDataCalculator
    into
    a
    `ContextMemoryHandler`
    who
    's job it is to manage and update the ContextMemory stuff as new information comes in
    -create
    a
    separate

    class or function that can receive and handle the `calcualte_memory_request` stuff

    -(feel free to suggest other refactor options)

    ```

    class MemoryDataCalculator(BaseModel):
        calculate_memory_request: CalculateMemoryRequest
        current_context_memory: ContextMemoryDocument = None
        message_history: MessageHistory
        max_tokens = CONVERSATION_HISTORY_MAX_TOKENS
        database_operations: BackendDatabaseOperations

        memory: ChatbotConversationMemory = ChatbotConversationMemory()

        @classmethod
        async def from_calculate_memory_request(cls,
                                                calculate_memory_request: CalculateMemoryRequest,
                                                database_operations: BackendDatabaseOperations, ):

            current_context_memory = await cls._get_current_context_memory(calculate_memory_request,
                                                                           database_operations)

            if current_context_memory is None:
                logger.warning(f"Context memory not found for request: {calculate_memory_request.context_route.dict()}")
                return

            message_history = await cls._get_message_history(calculate_memory_request, database_operations)

            if message_history is None:
                logger.warning(
                    f"Message history not found for request: {calculate_memory_request.context_route.dict()}")
                return

            logger.info(f"Loaded {len(message_history.get_all_messages())} messages from history for context route: "
                        f"{calculate_memory_request.context_route.friendly_path}")

            return cls(calculate_memory_request=calculate_memory_request,
                       current_context_memory=current_context_memory,
                       message_history=message_history,
                       limit_messages=calculate_memory_request.limit_messages,
                       database_operations=database_operations)

        @classmethod
        async def _get_message_history(cls, calculate_memory_request, database_operations):
            message_history = await database_operations.get_message_history_document(
                request=MessageHistoryRequest(context_route=calculate_memory_request.context_route,
                                              database_name=calculate_memory_request.database_name,
                                              limit_messages=calculate_memory_request.limit_messages))
            return message_history

        @classmethod
        async def _get_current_context_memory(cls, calculate_memory_request, database_operations):
            current_context_memory = await database_operations.get_context_memory_document(
                ContextMemoryRequest.build_get_request_from_context_route(
                    context_route=calculate_memory_request.context_route,
                    database_name=calculate_memory_request.database_name))
            return current_context_memory

        async def calculate(self,
                            upsert: bool = True,
                            overwrite: bool = False) -> ContextMemoryDocument:

            self.calculate_memory_from_history(message_history=self.message_history,
                                               limit_messages=self.calculate_memory_request.limit_messages,
                                               overwrite=overwrite)

            context_memory_document = ContextMemoryDocument(
                context_route=self.calculate_memory_request.context_route,
                message_buffer=[message.dict() for message in self.memory.buffer],
                summary=self.memory.moving_summary_buffer,
                summary_prompt=self.memory.prompt,
                token_count=self.memory.token_count,
            )

            if upsert:
                await self.database_operations.upsert_context_memory(
                    ContextMemoryRequest(data=context_memory_document,
                                         database_name=self.calculate_memory_request.database_name,
                                         query=self.calculate_memory_request.context_route.as_query))

            return context_memory_document

        def calculate_memory_from_history(self,
                                          message_history: MessageHistory,
                                          limit_messages: int = None,
                                          overwrite: bool = False):
            logger.info(
                f"Calculating memory from history for context route: {self.calculate_memory_request.context_route.friendly_path} using {len(message_history.get_all_messages())} messages...")

            previously_calculated_uuids = []
            if self.current_context_memory is not None:
                previously_calculated_uuids = self.current_context_memory.message_uuids

            message_count = -1
            for chat_message in message_history.get_all_messages():
                if chat_message.uuid in previously_calculated_uuids and not overwrite:
                    logger.trace(
                        f"Skipping message with uuid {chat_message.uuid} because it has already been incorporated into context memory.")
                    continue

                message_count += 1
                if limit_messages is not None:
                    logger.trace(f"Limiting messages to {limit_messages} - currently at {message_count}")
                    if message_count > limit_messages:
                        logger.trace(f"Reached limit of {limit_messages} messages. Breaking...")
                        break

                typed_message = self._create_typed_message(chat_message)
                logger.debug(f"Adding message to memory: {typed_message.dict()}")
                self.memory.chat_memory.add_message(typed_message)

                memory_token_length = self.memory.llm.get_num_tokens_from_messages(
                    messages=self.memory.chat_memory.messages)
                if memory_token_length > self.max_tokens:
                    logger.info(
                        f"Memory token length {memory_token_length} exceeds max tokens {self.max_tokens}. Pruning...")
                    logger.info(f"Memory summary before pruning: {self.memory.moving_summary_buffer}\n---\n")
                    self.memory.prune()
                    logger.info(f"Memory summary after pruning: {self.memory.moving_summary_buffer}")

            self.memory.moving_summary_buffer = self.memory.predict_new_summary(
                messages=self.memory.chat_memory.messages,
                existing_summary=self.memory.moving_summary_buffer)

        def _create_typed_message(self, chat_message: ChatMessage) -> Union[HumanMessage, AIMessage]:
            if chat_message.speaker.type == "human":
                human_message = self._create_human_message_from_chat_message(chat_message)
                logger.trace(f"Created human message: {human_message}")
                return human_message

            elif chat_message.speaker.type == "bot":
                ai_message = self._create_ai_message_from_chat_message(chat_message)
                logger.trace(f"Created AI message: {ai_message}")
                self.memory.chat_memory.add_message(ai_message)
                return ai_message

        def _create_ai_message_from_chat_message(self, chat_message):
            ai_message = AIMessage(
                content=f"{chat_message.content} - "
                        f"["
                        f"metadata - "
                        f"'username':{chat_message.speaker.name},"
                        f"'local_time': {chat_message.timestamp.human_readable_local},"
                        f"'notes': (this is you)"
                        f"]",
                additional_kwargs={**chat_message.dict(),
                                   "type": "ai"})
            return ai_message

        def _create_human_message_from_chat_message(self, chat_message):
            human_message = HumanMessage(
                content=f"{chat_message.content} "
                        f"["
                        f"metadata - "
                        f"'username':{chat_message.speaker.name},"
                        f"'local_time': {chat_message.timestamp.human_readable_local}"
                        f"]",
                additional_kwargs={**chat_message.dict(),
                                   "type": "human"})
            logger.trace(f"Adding human message: {human_message}")
            return human_message

    class ChatbotLLMChain:

        def __init__(self,
                     context_route: ContextRoute,
                     database_name: str,
                     database_operations: BackendDatabaseOperations,
                     chat_history_placeholder_name: str = "chat_history"):

            self.context_route = context_route
            self.database_name = database_name
            self.database_operations = database_operations
            self.model = ChatOpenAI(temperature=0.8,
                                    model_name="gpt-4",
                                    verbose=True,
                                    )
            self.prompt = ChatbotPrompt.build(chat_history_placeholder_name=chat_history_placeholder_name)

            self.memory = ChatbotConversationMemory()
            self.chain = self._build_chain()

        @classmethod
        async def from_context_route(cls,
                                     context_route: ContextRoute,
                                     database_name: str,
                                     database_operations: BackendDatabaseOperations):
            instance = cls(context_route=context_route,
                           database_name=database_name,
                           database_operations=database_operations)

            await instance.load_context_memory()
            return instance

        @property
        def _context_memory_get_request(self) -> ContextMemoryRequest:
            return ContextMemoryRequest.build_upsert_request_from_context_memory_document(
                document=self._context_memory_document,
                database_name=self.database_name)

        @property
        def _context_memory_upsert_request(self) -> ContextMemoryRequest:
            return ContextMemoryRequest.build_upsert_request_from_context_memory_document(
                document=self._context_memory_document,
                database_name=self.database_name)

        @property
        def _context_memory_document(self) -> ContextMemoryDocument:
            return ContextMemoryDocument.build(context_route=self.context_route,
                                               memory=self.memory)

        def _build_chain(self) -> RunnableSequence:
            return RunnableMap({
                "human_input": lambda x: x["human_input"],
                "memory": self.memory.load_memory_variables,
            }) | {
                "human_input": lambda x: x["human_input"],
                "chat_history": lambda x: x["memory"]["chat_memory"]
            } | self.prompt | self.model

        async def execute(self, message_string: str, pause_at_end: float = 1.0) -> AsyncIterable[str]:
            inputs = {"human_input": message_string}
            response_message = ""
            try:
                async for token in self.chain.astream(inputs):
                    logger.trace(f"Yielding token: {repr(token.content)}")
                    response_message += token.content
                    yield token.content
                yield STOP_STREAMING_TOKEN

                await asyncio.sleep(pause_at_end)  # give it a sec to clear the buffer

                logger.debug(f"Successfully executed chain! - Saving context to memory...")

                self._update_memory(inputs=inputs,
                                    outputs={"output": response_message})
                await self.upsert_context_memory()

                logger.trace(f"Response message: {response_message}")
            except Exception as e:
                logger.exception(e)
                raise

        async def load_context_memory(self):
            logger.info(f"Loading context memory for context route: {self.context_route.dict()}")
            document: ContextMemoryDocument = await self.database_operations.get_context_memory_document(
                self._context_memory_get_request)

            if document is None:
                logger.warning(
                    f"Could not load context memory from database for context route: {self._context_memory_get_request.query}")
            else:
                await self._configure_memory(document)

        async def _configure_memory(self, document: ContextMemoryDocument):
            self.memory.load_messages_from_message_buffer(buffer=document.message_buffer)
            self.memory.moving_summary_buffer = document.summary
            self.memory.prompt = document.summary_prompt

        async def upsert_context_memory(self):
            logger.debug(f"Upserting context memory for context route: {self.context_route.dict()}")
            try:
                await self.database_operations.upsert_context_memory(self._context_memory_upsert_request)
            except Exception as e:
                logger.exception(e)
                raise

        def _update_memory(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
            # TODO - sauce up the memory like we do int he memory calculator
            self.memory.save_context(inputs=inputs,
                                     outputs=outputs)

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

        def load_messages_from_message_buffer(self, buffer: List[Dict[str, Any]]) -> List[
            Union[HumanMessage, AIMessage]]:
            messages = []
            try:
                for message_dict in buffer:
                    if message_dict["additional_kwargs"]["type"] == "human":
                        messages.append(HumanMessage(**message_dict))
                    elif message_dict["additional_kwargs"]["type"] == "ai":
                        messages.append(AIMessage(**message_dict))
                self.chat_memory.messages = messages
            except Exception as e:
                logger.exception(e)
                raise

    logger = get_logger()

    class BackendDatabaseOperations(BaseModel):
        mongo_database: MongoDatabaseManager

        class Config:
            arbitrary_types_allowed = True

        @classmethod
        async def build(cls):
            mongo_database = await get_or_create_mongo_database_manager()
            return cls(mongo_database=mongo_database)

        async def upsert_discord_messages(self,
                                          request: UpsertDiscordMessagesRequest) -> UpsertDiscordMessagesResponse:
            logger.info(
                f"Upserting {len(request.data)} messages to database: {request.database_name} with query: {request.query}")

            success = await self.mongo_database.upsert_discord_messages(
                request=request)
            if success:
                return UpsertDiscordMessagesResponse(success=True)
            else:
                return UpsertDiscordMessagesResponse(success=False)

        async def get_message_history_document(self,
                                               request: MessageHistoryRequest) -> MessageHistory:
            logger.info(
                f"Getting conversation history for context route: {request.context_route.dict()}")
            message_history = await self.mongo_database.get_message_history(request=request)

            return message_history

        async def get_context_memory_document(self,
                                              request: ContextMemoryRequest) -> Optional[ContextMemoryDocument]:
            if request.request_type == "upsert":
                raise Exception("get_context_memory_document should not be called with request type: upsert")

            logger.info(
                f"Retrieving context memory for context route: {request.data.context_route.as_flat_dict}")
            context_memory_document = await self.mongo_database.get_context_memory(request=request)
            if context_memory_document is None:
                logger.warning(f"Context memory not found for context route: {request.data.context_route.as_flat_dict}")
                return None

            return context_memory_document

        async def upsert_context_memory(self, request: ContextMemoryRequest):
            logger.info(
                f"Updating context memory for context route: {request.data.context_route.dict()}")
            success = await self.mongo_database.upsert_context_memory(request=request, )
            if success:
                logger.success(
                    f"Successfully updated context memory for context route: {request.data.context_route.dict()}")
            else:
                logger.error(
                    f"Error occurred while updating context memory for context route: {request.data.context_route.dict()}")

        async def close(self):
            logger.info("Closing database connection...")
            await self.mongo_database.close()
            logger.info("Database connection closed!")
