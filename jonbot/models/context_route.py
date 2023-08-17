from enum import Enum
from typing import Optional, Literal

import discord
from pydantic import BaseModel, validator


class Frontends(Enum):
    DISCORD = 'discord'
    TELEGRAM = 'telegram'
    OTHER = 'other'
frontend_types = tuple(value.value for value in Frontends)

class SubContextComponentTypes(Enum):
    SERVER = 'server'
    DIRECT_MESSAGE = 'direct_message'
    CHANNEL = 'channel'
    THREAD = 'thread'
    UNKNOWN = 'unknown'
    DUMMY = 'dummy'
    OTHER = 'other'


subcontext_types = tuple(value.value for value in SubContextComponentTypes)
class SubContextComponent(BaseModel):
    """Represents a component with name and id"""
    type: Literal[subcontext_types]
    name: str
    id: int
    parent: Optional[str] = None

    def __str__(self):
        return f"{self.type}-{self.name}-{self.id}"


class ContextRoute(BaseModel):
    """How to grab this context route from the database"""
    frontend: Literal[frontend_types]
    server: SubContextComponent
    channel: SubContextComponent
    thread: Optional[SubContextComponent] = None


    @classmethod
    def from_discord_message(cls, message: discord.Message):
        frontend = Frontends.DISCORD.value
        if message.guild:
            server = SubContextComponent(name=f"{message.guild.name}",
                                         id=message.guild.id,
                                         parent=frontend,
                                         type=SubContextComponentTypes.SERVER.value, )

            if "thread" in message.channel.type.name:

                channel = SubContextComponent(name=f"{message.channel.parent.name}",
                                              id=message.channel.parent.id,
                                              parent=str(server),
                                              type=SubContextComponentTypes.CHANNEL.value, )

                thread = SubContextComponent(name=f"{message.channel.name}",
                                             id=message.channel.id,
                                             parent=str(channel),
                                             type=SubContextComponentTypes.THREAD.value,
                                             )
            else:  # Direct Message
                thread = None
                channel = SubContextComponent(name=f"{message.channel.name}",
                                              id=message.channel.id,
                                              parent=str(frontend),
                                              type=SubContextComponentTypes.DIRECT_MESSAGE.value,
                                              )


        else:  # DM
            server = SubContextComponent(name='DirectMessage',
                                         id=message.channel.id,
                                         parent=str(frontend))
            channel = SubContextComponent(name=f"channel-{message.channel.name}",
                                          id=message.channel.id)
            thread = None

        return cls(frontend=frontend,
                   server=server,
                   channel=channel,
                   thread=thread,
                   )

    @property
    def as_path(self):
        if self.thread:
            return f"frontend-{self.frontend}/{str(self.server)}/{str(self.channel)}/{str(self.thread)}/"
        else:
            return f"frontend-{self.frontend}/{str(self.server)}/{str(self.channel)}/messages/"

    @property
    def as_query(self):
        return {"frontend": self.frontend,
                "server_id": self.server.id,
                "channel_id": self.channel.id,
                "thread_id": self.thread.id if self.thread else ''
                }

    @classmethod
    def dummy(cls, dummy_text: str):
        frontend = Frontends.OTHER.value
        server = SubContextComponent(type=SubContextComponentTypes.SERVER.value,
                                     name=dummy_text,
                                     parent=frontend,
                                     id=0)
        channel = SubContextComponent(type=SubContextComponentTypes.CHANNEL.value,
                                      name=dummy_text,
                                      parent=str(server),
                                      id=0)
        thread = SubContextComponent(type=SubContextComponentTypes.THREAD.value,
                                     name=dummy_text,
                                     parent=str(channel),
                                     id=0)
        return cls(frontend=frontend,
                   server=server,
                   channel=channel,
                   thread=thread,
                   )
