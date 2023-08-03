import os

import aiofiles
import aiohttp
import openai
from pydub import AudioSegment


async def transcribe_audio(
    audio_file_url: str,
    prompt: str = None,
    response_format: str = None,
    temperature: float = None,
    language: str = None
) -> str:
    ogg_file_path = f"/tmp/voice-message.ogg"
    mp3_file_path = f"/tmp/voice-message.mp3"

    async with aiohttp.ClientSession() as session:
        async with session.get(audio_file_url) as response:
            if response.status == 200:
                async with aiofiles.open(ogg_file_path, mode='wb') as file:
                    await file.write(await response.read())
                print("File downloaded successfully.")
            else:
                print("Failed to download file.")
                return "Failed to download file."

    try:
        # Convert ogg to mp3
        audio = AudioSegment.from_ogg(ogg_file_path)
        audio.export(mp3_file_path, format="mp3")

        # Open the audio file
        with open(mp3_file_path, "rb") as audio_file:
            # Call OpenAI's Whisper model for transcription
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                language=language
            )

        os.remove(ogg_file_path)  # Optional: Remove the temporary ogg file
        os.remove(mp3_file_path)  # Optional: Remove the temporary mp3 file

        # Extracting the transcript
        return transcript['text']
    except Exception as e:
        print(f"An error occurred while transcribing: {str(e)}")
        return "An error occurred while transcribing."
