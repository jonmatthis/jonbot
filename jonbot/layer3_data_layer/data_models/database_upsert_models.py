from pydantic import BaseModel


class DatabaseUpsertRequest(BaseModel):
    collection: str
    data: dict
    query: dict


class DatabaseUpsertResponse(BaseModel):
    success: bool
