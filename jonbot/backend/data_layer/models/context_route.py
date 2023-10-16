from enum import Enum
from typing import Optional, Union, List

import discord
from pydantic import BaseModel


class SubContextComponentTypes(str, Enum):
    SERVER = "server"
    DIRECT_MESSAGE = "direct_message"
    CHANNEL = "channel"
    THREAD = "thread"
    FORUM = "forum"
    CATEGORY = "category"
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

    @classmethod
    def create_dummy(cls,
                     dummy_text: str = "dummy",
                     parent: str = None,
                     id: int = 0):
        return cls(
            type=SubContextComponentTypes.DUMMY.value,
            name=dummy_text,
            id=id,
            parent=parent,
        )


class Frontends(str, Enum):
    DISCORD = "discord"
    TELEGRAM = "telegram"
    OTHER = "other"


class ContextRoute(BaseModel):
    """How to grab this context route from the database"""

    frontend: Frontends
    server: SubContextComponent
    category: SubContextComponent
    channel: SubContextComponent
    thread: SubContextComponent

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
            if hasattr(message.channel, "category"):
                if "thread" in (str(message.channel.type)).lower():
                    category = SubContextComponent(
                        name=f"{message.channel.parent.name}",
                        id=message.channel.parent.id,
                        parent=str(server),
                        type=SubContextComponentTypes.CATEGORY.value,
                    )
                elif not message.channel.category:
                    category = SubContextComponent.create_dummy(dummy_text="TopLevel",
                                                                parent=str(server))
                else:
                    category = SubContextComponent(
                        name=f"{message.channel.category.name}",
                        id=message.channel.category.id,
                        parent=str(server),
                        type=SubContextComponentTypes.CATEGORY.value,
                    )
            else:
                category = SubContextComponent.create_dummy(dummy_text="no_category",
                                                            parent=str(server))

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
            else:  # top level channel
                thread = SubContextComponent.create_dummy(dummy_text="top_level",
                                                          parent=str(server))
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
            category = SubContextComponent.create_dummy(dummy_text="DM0Cha",
                                                        parent=str(server))
            channel = SubContextComponent(
                name=f"DM-{message.channel.id}",
                id=message.channel.id,
                parent=str(server),
                type=SubContextComponentTypes.CHANNEL.value,
            )
            thread = SubContextComponent.create_dummy(dummy_text="DM-chat",
                                                      parent=str(channel))

        return cls(
            frontend=frontend,
            server=server,
            category=category,
            channel=channel,
            thread=thread,
        )

    @property
    def friendly_path(self):
        return f"{self.frontend.value}/{self.server.name}/{self.category.name}/{self.channel.name}/threads/{self.thread.name}/messages/"

    @property
    def full_path(self):
        return f"frontend-{self.frontend}/{str(self.server)}/{str(self.category)}/{str(self.channel)}/threads/{str(self.thread)}/"

    @property
    def as_query(self) -> dict:
        query = {
            "frontend": self.frontend.value,
            "server_id": self.server.id,
            "category_id": self.category.id,
            "channel_id": self.channel.id,
            "thread_id": self.thread.id
        }
        return query

    @property
    def as_tree_path(self) -> List[Union[str, int]]:
        return list(self.friendly_path.split("/"))

    @property
    def as_flat_dict(self):
        return {
            "server_name": self.server.name,
            "server_id": self.server.id,
            "category_name": self.category.name,
            "category_id": self.category.id,
            "channel_name": self.channel.name,
            "channel_id": self.channel.id,
            "thread_name": self.thread.name,
            "thread_id": self.thread.id,
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
