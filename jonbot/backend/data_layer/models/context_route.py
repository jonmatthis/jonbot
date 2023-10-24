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
        frontend_component = Frontends.DISCORD.value
        if message.guild:
            server_component = SubContextComponent(
                name=f"{message.guild.name}",
                id=message.guild.id,
                parent=frontend_component,
                type=SubContextComponentTypes.SERVER.value,
            )
            if hasattr(message.channel, "category"):
                if message.channel.category:
                    category_component = SubContextComponent(
                        name=f"{message.channel.category.name}",
                        id=message.channel.category.id,
                        parent=str(server_component),
                        type=SubContextComponentTypes.CATEGORY.value,
                    )
                else:
                    category_component = SubContextComponent.create_dummy(dummy_text="TopLevel",
                                                                          parent=str(server_component))
            else:
                category_component = SubContextComponent.create_dummy(dummy_text="no_category",
                                                                      parent=str(server_component))

            if "thread" in message.channel.type.name.lower():
                channel_component = SubContextComponent(
                    name=f"{message.channel.parent.name}",
                    id=message.channel.parent.id,
                    parent=str(server_component),
                    type=SubContextComponentTypes.CHANNEL.value,
                )

                thread_component = SubContextComponent(
                    name=f"{message.channel.name}",
                    id=message.channel.id,
                    parent=str(channel_component),
                    type=SubContextComponentTypes.THREAD.value,
                )
            else:  # top level message
                channel_component = SubContextComponent(
                    name=f"{message.channel.name}",
                    id=message.channel.id,
                    parent=str(server_component),
                    type=SubContextComponentTypes.CHANNEL.value,
                )
                if message.thread:
                    thread_component = SubContextComponent(
                        name=f"{message.thread.name}",
                        id=message.thread.id,
                        parent=str(channel_component),
                        type=SubContextComponentTypes.THREAD.value,
                    )
                else:
                    thread_component = SubContextComponent.create_dummy(dummy_text="no_thread",
                                                                        parent=str(server_component))
        else:  # DM
            server_component = SubContextComponent(
                name="DirectMessage",
                id=message.channel.id,
                parent=str(frontend_component),
                type=SubContextComponentTypes.DIRECT_MESSAGE.value,
            )
            category_component = SubContextComponent.create_dummy(dummy_text="DM-Chat",
                                                                  parent=str(server_component))
            channel_component = SubContextComponent(
                name=f"DM-{message.channel.id}",
                id=message.channel.id,
                parent=str(server_component),
                type=SubContextComponentTypes.CHANNEL.value,
            )
            thread_component = SubContextComponent.create_dummy(dummy_text="DM-chat",
                                                                parent=str(channel_component))

        return cls(
            frontend=frontend_component,
            server=server_component,
            category=category_component,
            channel=channel_component,
            thread=thread_component,
        )

    @property
    def friendly_path(self):
        path = f"{self.frontend.value}/{self.server.name}/{self.category.name}/{self.channel.name}/threads/{self.thread.name}/messages/"
        return path.replace(" ", "_")

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
        return [value for key, value in self.as_flat_dict.items() if key.endswith("_id")]

    @property
    def as_friendly_tree_path(self) -> List[str]:
        path = []
        for key, value in self.as_flat_dict.items():
            if key.endswith("_name"):
                thing = key.replace("_name", "")
                id = self.as_flat_dict[f"{thing}_id"]
                path.append(f"{value.replace(' ', '_')}-{id}")
        return path

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
