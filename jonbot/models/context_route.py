from enum import Enum
from typing import Optional

import discord
from pydantic import BaseModel


class SubContextComponentTypes(str, Enum):
    SERVER = "server"
    DIRECT_MESSAGE = "direct_message"
    CHANNEL = "channel"
    THREAD = "thread"
    FORUM = "forum"
    UNKNOWN = "unknown"
    DUMMY = "dummy"
    OTHER = "other"


class SubContextComponent(BaseModel):
    """Represents a component with name and id"""

    type: SubContextComponentTypes
    name: str
    id: int
    parent: Optional[str] = None

    def __str__(self):
        return f"{self.type}-{self.name}-{self.id}"

    def as_sub_dict(self):
        return {"name": self.name, "id": self.id, "parent": self.parent}


class Frontends(str, Enum):
    DISCORD = "discord"
    TELEGRAM = "telegram"
    OTHER = "other"


class ContextRoute(BaseModel):
    """How to grab this context route from the database"""

    frontend: Frontends
    server: SubContextComponent
    channel: SubContextComponent
    thread: Optional[SubContextComponent] = None

    @classmethod
    def from_discord_channel(cls, channel: discord.TextChannel):
        return cls.from_discord_message(message=channel.last_message)

    @classmethod
    def from_discord_message(cls, message: discord.Message):
        frontend = Frontends.DISCORD.value
        if message.guild:
            server = SubContextComponent(
                name=f"{message.guild.name}",
                id=message.guild.id,
                parent=frontend,
                type=SubContextComponentTypes.SERVER.value,
            )

            if "thread" in message.channel.type.name:
                channel = SubContextComponent(
                    name=f"{message.channel.parent.name}",
                    id=message.channel.parent.id,
                    parent=str(server),
                    type=SubContextComponentTypes.CHANNEL.value,
                )

                thread = SubContextComponent(
                    name=f"{message.channel.name}",
                    id=message.channel.id,
                    parent=str(channel),
                    type=SubContextComponentTypes.THREAD.value,
                )
            else:  # Direct Message
                thread = None
                channel = SubContextComponent(
                    name=f"{message.channel.name}",
                    id=message.channel.id,
                    parent=str(server),
                    type=SubContextComponentTypes.CHANNEL.value,
                )

        else:  # DM
            server = SubContextComponent(
                name="DirectMessage",
                id=message.channel.id,
                parent=str(frontend),
                type=SubContextComponentTypes.DIRECT_MESSAGE.value,
            )
            channel = SubContextComponent(
                name=f"DM-{message.channel.id}",
                id=message.channel.id,
                parent=str(server),
                type=SubContextComponentTypes.CHANNEL.value,
            )
            thread = None

        return cls(
            frontend=frontend,
            server=server,
            channel=channel,
            thread=thread,
        )

    @property
    def friendly_path(self):
        if self.thread:
            return f"{self.frontend}/{self.server.name}/{self.channel.name}/threads/{self.thread.name}/messages/"
        else:
            return f"{self.frontend}/{self.server.name}/{self.channel.name}/messages/"

    @property
    def full_path(self):
        if self.thread:
            return f"frontend-{self.frontend}/{str(self.server)}/{str(self.channel)}/threads/{str(self.thread)}/messages/"
        else:
            return f"frontend-{self.frontend}/{str(self.server)}/{str(self.channel)}/messages/"

    @property
    def as_query(self) -> dict:
        query = {
            "frontend": self.frontend.value,
            "server_id": self.server.id,
            "channel_id": self.channel.id,
        }
        if self.thread:
            query.update({"thread_id": self.thread.id})

        return query

    @property
    def as_flat_dict(self):
        return {
            "server_name": self.server.name,
            "server_id": self.server.id,
            "channel_name": self.channel.name,
            "channel_id": self.channel.id,
            "thread_name": self.thread.name if self.thread else None,
            "thread_id": self.thread.id if self.thread else None,
        }

    @classmethod
    def dummy(cls, dummy_text: str):
        frontend = Frontends.OTHER.value
        server = SubContextComponent(
            type=SubContextComponentTypes.SERVER.value,
            name=dummy_text,
            parent=frontend,
            id=0,
        )
        channel = SubContextComponent(
            type=SubContextComponentTypes.CHANNEL.value,
            name=dummy_text,
            parent=str(server),
            id=0,
        )
        thread = SubContextComponent(
            type=SubContextComponentTypes.THREAD.value,
            name=dummy_text,
            parent=str(channel),
            id=0,
        )
        return cls(
            frontend=frontend,
            server=server,
            channel=channel,
            thread=thread,
        )
