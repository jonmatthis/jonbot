import uuid

from pydantic import BaseModel, Field


class VoiceToTextRequest(BaseModel):
    audio_file_url: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = None
    response_format: str = None
    temperature: float = None
    language: str = None


class VoiceToTextResponse(BaseModel):
    text: str
