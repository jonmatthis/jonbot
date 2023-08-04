import uuid
from datetime import datetime
from typing import Union, List

import discord
from pydantic import BaseModel

from chatbot.ai.assistants.course_assistant.course_assistant import CourseAssistant
from chatbot.ai.assistants.video_chatter.video_chatter import VideoChatter


class Chat(BaseModel):
    title: str
    thread: discord.Thread
    assistant: Union[CourseAssistant, VideoChatter]

    started_at: str = datetime.now().isoformat()
    chat_id: str = uuid.uuid4()

    class Config:
        arbitrary_types_allowed = True
