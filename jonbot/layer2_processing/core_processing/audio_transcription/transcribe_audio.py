import os

import aiofiles
import aiohttp
import openai
from pydub import AudioSegment

from jonbot import get_logger

logger = get_logger()


async def transcribe_audio_function(
        audio_file_url: str,
        prompt: str = None,
        response_format: str = None,
        temperature: float = None,
        language: str = None,
) -> str:
    TEMP_FILE_PATH = f"/tmp/voice-message"

    file_extension = audio_file_url.split('.')[-1]  # Get the audio file extension from the URL
    original_file_path = f"{TEMP_FILE_PATH}.{file_extension}"
    mp3_file_path = f"{TEMP_FILE_PATH}.mp3"

    async with aiohttp.ClientSession() as session:
        async with session.get(audio_file_url) as response:
            if response.status == 200:
                async with aiofiles.open(original_file_path, mode='wb') as file:
                    await file.write(await response.read())
                logger.info("Audio file downloaded successfully.")
            else:
                logger.info("Audio file failed to download.")
                return "Failed to download file."

    try:
        # Convert audio to mp3 based on its format
        if file_extension == 'ogg':
            audio = AudioSegment.from_ogg(original_file_path)
        elif file_extension == 'wav':
            audio = AudioSegment.from_wav(original_file_path)
        elif file_extension == 'mp3':
            audio = AudioSegment.from_mp3(original_file_path)
        # Add more formats as needed
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        audio.export(mp3_file_path, format="mp3")

        # Open the audio file
        with open(mp3_file_path, "rb") as audio_file:
            # Call OpenAI's Whisper model for transcription
            transcription_response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                language=language
            )

        try:
            os.remove(original_file_path)  # Optional: Remove the original audio file
        except FileNotFoundError:
            pass

        try:
            os.remove(mp3_file_path)  # Optional: Remove the temporary mp3 file
        except FileNotFoundError:
            pass

        # Extracting the transcript
        return transcription_response.text
    except Exception as e:
        logger.exception(f"An error occurred while transcribing: {str(e)}")
        return "An error occurred while transcribing."
