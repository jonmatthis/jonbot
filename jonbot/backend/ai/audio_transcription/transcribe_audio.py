import mimetypes
import os
from pathlib import Path

import aiofiles
import aiohttp
import openai
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment

from jonbot.backend.data_layer.models.voice_to_text_request import VoiceToTextResponse
from jonbot.system.path_getters import get_temp_folder
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()


def save_mp3_from_video(original_file_path, mp3_file_path):
    video = VideoFileClip(str(original_file_path))
    audio = video.audio
    audio.write_audiofile(str(mp3_file_path))
    video.close()
    audio.close()


def save_mp3_from_audio(original_file_path, mp3_file_path):
    format_name = original_file_path.suffix.lstrip('.')
    audio = AudioSegment.from_file(str(original_file_path), format=format_name)
    audio.export(mp3_file_path, format="mp3")
    audio.close()


async def transcribe_audio_function(
        audio_file_url: str,
        prompt: str = None,
        response_format: str = None,
        temperature: float = None,
        language: str = None,
) -> VoiceToTextResponse:
    file_name = "audio-file"
    file_extension = audio_file_url.split(".")[-1]  # Get the audio file extension from the URL
    file_extension = file_extension.split("?")[0]  # Remove any query parameters
    original_file_name = f"{file_name}.{file_extension}"
    original_file_path = Path(get_temp_folder()) / original_file_name

    mp3_file_name = f"{file_name}.mp3"
    mp3_file_path = Path(get_temp_folder()) / mp3_file_name
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_file_url) as response:
                if response.status == 200:
                    async with aiofiles.open(original_file_path, mode="wb") as file:
                        await file.write(await response.read())
                    logger.info("Audio file downloaded successfully.")
                else:
                    logger.info("Audio file failed to download.")
                    raise Exception("Audio file failed to download.")

        mimetype = mimetypes.guess_type(original_file_path)[0]

        # Convert to mp3 based on its format
        if mimetype and 'video' in mimetype:
            save_mp3_from_video(original_file_path, mp3_file_path)
        elif mimetype and 'audio' in mimetype:
            save_mp3_from_audio(original_file_path, mp3_file_path)
        else:
            raise ValueError(f"Unsupported file format: {mimetype}")

        if not Path(mp3_file_path).exists():
            raise FileNotFoundError(
                f"Could not find mp3 file at {mp3_file_path} - failed to extract audio from this URL: {audio_file_url}")

        with open(mp3_file_path, "rb") as audio_file:
            # Call OpenAI's Whisper model for transcription
            transcription_response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                language=language,
            )

        if transcription_response:
            logger.success(
                f"Transcription successful! {transcription_response['text']}"
            )
        else:
            raise Exception("Transcription request returned None.")

        os.remove(original_file_path)  # Remove the original audio file

        return VoiceToTextResponse(
            text=transcription_response.text,
            success=True,
            response_time_ms=transcription_response.response_ms,
            mp3_file_path=str(mp3_file_path),
        )
    except Exception as e:
        logger.exception(f"An error occurred while transcribing: {str(e)}")
        raise
