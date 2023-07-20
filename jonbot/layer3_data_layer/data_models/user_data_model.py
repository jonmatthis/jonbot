from typing import List

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    user_id: str
    identifiers: dict = {}
    conversations: List[str] = Field(default_factory=list, description="list of the user's conversation ids")
    metadata: dict = {}
