import uuid

from pydantic import BaseModel, Field


class VoiceToTextRequest(BaseModel):
    audio_file_url: str
    prompt: str = None
    response_format: str = None
    temperature: float = None
    language: str = None


class VoiceToTextResponse(BaseModel):
    success: bool
    text: str = None
    response_time: float = None
    mp3_file_path: str = None
