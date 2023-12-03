from typing import Optional, Dict, Any

from pydantic import BaseModel


class VoiceToTextRequest(BaseModel):
    audio_source: str
    prompt: str = None
    response_format: str = None
    temperature: float = None
    language: str = None
    metadata: Optional[Dict[Any, Any]] = None


class VoiceToTextResponse(BaseModel):
    success: bool
    text: str = None
    response_time: float = None
    mp3_file_path: str = None
