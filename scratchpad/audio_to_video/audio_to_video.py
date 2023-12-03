import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path

from pydub import AudioSegment

from jonbot.backend.ai.image_generation.image_generator import ImageGenerator
from jonbot.system.path_getters import get_base_data_folder_path

# Constants
CHUNK_LENGTH_MS = 7000
OVERLAP_MS = 6000
SESSION_FOLDER_NAME = datetime.now().strftime("%Y-%m-%d_%H_%M_%S_%Z")
OUTPUT_FOLDER = str(Path(get_base_data_folder_path()) / "audio_to_video" / SESSION_FOLDER_NAME)

from openai import AsyncOpenAI

openai_client = AsyncOpenAI()
image_generator = ImageGenerator()


async def process_chunk(chunk: AudioSegment,
                        chunk_start: int,
                        output_folder: str):
    chunk_filename = f'temp_chunk_{chunk_start}.ogg'
    chunk.export(chunk_filename, format='ogg')

    with open(chunk_filename, "rb") as chunk_file:
        transcript = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=chunk_file,
            response_format="verbose_json"
        )

    os.remove(chunk_filename)

    # Generate image from transcription
    image_path = await image_generator.generate_image(transcript.text,
                                                      size="1024x1024",
                                                      quality="standard",
                                                      )
    new_image_filename = os.path.join(output_folder,
                                      f"frame_{chunk_start // OVERLAP_MS}_chunk_start_{chunk_start}_ms.png")
    shutil.copy(image_path, new_image_filename)


async def audio_to_video(audio_file_path: str,
                         output_folder_path: str,
                         chunk_length_ms: int = CHUNK_LENGTH_MS,
                         overlap_ms: int = OVERLAP_MS):
    Path(output_folder_path).mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(audio_file_path)
    chunk_starts = list(range(0, len(audio), chunk_length_ms - overlap_ms))

    tasks = []
    for chunk_start in chunk_starts:
        chunk_end = min(chunk_start + chunk_length_ms, len(audio))
        chunk = audio[chunk_start:chunk_end]
        await process_chunk(chunk, chunk_start, output_folder_path)

    print("Processing completed!")


if __name__ == "__main__":
    audiofile_path = r"C:\Users\jonma\Downloads\voice-message(7).ogg"
    asyncio.run(audio_to_video(audio_file_path=audiofile_path, output_folder_path=OUTPUT_FOLDER))
