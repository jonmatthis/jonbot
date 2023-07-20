import uuid
from datetime import datetime

import discord
from pydantic import BaseModel

from golem_garden.backend.ai.chatbot.chatbot import Chatbot


class ThreadChat(BaseModel):
    title: str
    thread: discord.Thread
    assistant: Chatbot

    started_at: str = datetime.now().isoformat()
    chat_id: str = uuid.uuid4()

    class Config:
        arbitrary_types_allowed = True
