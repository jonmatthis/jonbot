import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from pydub import AudioSegment

from jonbot.backend.ai.audio_transcription.transcribe_audio import transcribe_audio
from jonbot.backend.ai.image_generation.image_generator import ImageGenerator
from jonbot.system.path_getters import get_base_data_folder_path
from scratchpad.audio_to_video.video_from_frames import generate_video_from_images

# Constants
CHUNK_LENGTH_MS = 7000
OVERLAP_MS = 1000
SESSION_FOLDER_NAME = datetime.now().strftime("%Y-%m-%d_%H_%M_%S_%Z")
OUTPUT_FOLDER = str(Path(get_base_data_folder_path()) / "audio_to_video" / SESSION_FOLDER_NAME)

image_generator = ImageGenerator()


async def transcribe_audio_chunk(chunk: AudioSegment, chunk_start: int, prompt: str = None):
    chunk_filename = f'temp_chunk_{chunk_start}.ogg'
    chunk.export(chunk_filename, format='ogg')
    transcription = await transcribe_audio(audio_source=chunk_filename, prompt=prompt)
    os.remove(chunk_filename)
    return transcription.text, chunk_start


async def audio_transcription_to_json(audio_file_path: str, output_folder_path: str, prompt: str = None) -> Dict[
    int, Dict[str, str]]:
    Path(output_folder_path).mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(audio_file_path)
    chunk_starts = list(range(0, len(audio), CHUNK_LENGTH_MS - OVERLAP_MS))

    transcriptions = {}
    for chunk_start in chunk_starts:
        chunk_end = min(chunk_start + CHUNK_LENGTH_MS, len(audio))
        chunk = audio[chunk_start:chunk_end]
        transcription_text, chunk_start_ms = await transcribe_audio_chunk(chunk=chunk, chunk_start=chunk_start,
                                                                          prompt=prompt)
        # Save transcription info
        transcriptions[chunk_start_ms] = {
            "text": transcription_text,
            "image_filename": f"frame_{chunk_start // OVERLAP_MS}_chunk_start_{chunk_start}_ms.png"
        }

    # Save transcriptions to JSON
    json_path = Path(output_folder_path) / 'transcriptions.json'
    with json_path.open('w') as json_file:
        json.dump(transcriptions, json_file, indent=4)

    return transcriptions


async def generate_images_from_json(transcriptions: Dict[int, Dict[str, str]],
                                    output_folder_path: str):
    for chunk_start_ms, transcription_info in transcriptions.items():
        image_path = await image_generator.generate_image(transcription_info['text'])
        new_image_filename = os.path.join(output_folder_path, transcription_info['image_filename'])
        os.rename(image_path, new_image_filename)


async def main(audio_file_path: str, output_folder_path: str, prompt: str = None):
    transcriptions = await audio_transcription_to_json(audio_file_path=audio_file_path,
                                                       output_folder_path=output_folder_path,
                                                       prompt=prompt)
    await generate_images_from_json(transcriptions=transcriptions,
                                    output_folder_path=output_folder_path)

    generate_video_from_images(path_to_images=output_folder_path,
                               audio_file_path=audio_file_path,
                               image_format="png",
                               desired_frame_rate=30,
                               output_video_name="output_video.mp4")
    print("Processing completed!")


if __name__ == "__main__":
    audiofile_path = r"C:\Users\jonma\Downloads\3721a173376720036c847e1677198d8e.mp4"
    asyncio.run(main(audio_file_path=audiofile_path, output_folder_path=OUTPUT_FOLDER))

    # or load from json
    # output_folder = Path(r"C:\Users\jonma\None_data\audio_to_video\2023-12-03_13_33_55_")
    # json_path = output_folder / 'transcriptions.json'
    # with open(json_path, 'r') as json_file:
    #     transcriptions = json.load(json_file)
    # asyncio.run(generate_images_from_json(transcriptions=transcriptions,
    #                                       output_folder_path=str(output_folder)))

# import asyncio
# import os
# import shutil
# from datetime import datetime
# from pathlib import Path
#
# from pydub import AudioSegment
#
# from jonbot.backend.ai.audio_transcription.transcribe_audio import transcribe_audio
# from jonbot.backend.ai.image_generation.image_generator import ImageGenerator
# from jonbot.system.path_getters import get_base_data_folder_path
# from scratchpad.audio_to_video.video_from_frames import generate_video_from_images
#
# # Constants
# CHUNK_LENGTH_MS = 10000
# OVERLAP_MS = 1000
# SESSION_FOLDER_NAME = datetime.now().strftime("%Y-%m-%d_%H_%M_%S_%Z")
# OUTPUT_FOLDER = str(Path(get_base_data_folder_path()) / "audio_to_video" / SESSION_FOLDER_NAME)
#
# from openai import AsyncOpenAI
#
# openai_client = AsyncOpenAI()
# image_generator = ImageGenerator()
#
#
# async def process_chunk(chunk: AudioSegment,
#                         chunk_start: int,
#                         output_folder: str,
#                         prompt: str = None):
#     chunk_filename = f'temp_chunk_{chunk_start}.ogg'
#     chunk.export(chunk_filename, format='ogg')
#     response = await transcribe_audio(audio_source=chunk_filename,
#                                       prompt=prompt)
#
#     os.remove(chunk_filename)
#
#     # Generate image from transcription
#     image_path = await image_generator.generate_image(response.text,
#                                                       size="1024x1024",
#                                                       quality="standard",
#                                                       )
#     new_image_filename = os.path.join(output_folder,
#                                       f"frame_{chunk_start // OVERLAP_MS}_chunk_start_{chunk_start}_ms.png")
#     shutil.copy(image_path, new_image_filename)
#
#
# async def audio_to_video(audio_file_path: str,
#                          output_folder_path: str,
#                          prompt: str = None,
#                          chunk_length_ms: int = CHUNK_LENGTH_MS,
#                          overlap_ms: int = OVERLAP_MS):
#     Path(output_folder_path).mkdir(parents=True, exist_ok=True)
#     audio = AudioSegment.from_file(audio_file_path)
#     chunk_starts = list(range(0, len(audio), chunk_length_ms - overlap_ms))
#
#     tasks = []
#     for chunk_start in chunk_starts:
#         chunk_end = min(chunk_start + chunk_length_ms, len(audio))
#         chunk = audio[chunk_start:chunk_end]
#         await process_chunk(chunk=chunk,
#                             chunk_start=chunk_start,
#                             output_folder=output_folder_path,
#                             prompt=prompt)
#
#     generate_video_from_images(path_to_images=output_folder_path,
#                                audio_file_path=audio_file_path,
#                                image_format="png",
#                                desired_frame_rate=30,
#                                output_video_name="output_video.mp4")
#     print("Processing completed!")
#
#
# if __name__ == "__main__":
#     audiofile_path = r"C:\Users\jonma\Downloads\3721a173376720036c847e1677198d8e.mp4"
#     asyncio.run(audio_to_video(audio_file_path=audiofile_path, output_folder_path=OUTPUT_FOLDER))
