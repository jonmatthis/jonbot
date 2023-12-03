import os
import subprocess
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from natsort import natsorted
from pydub import AudioSegment

from jonbot.backend.ai.audio_transcription.transcribe_audio import convert_to_mp3


def simple_interpolate_frames(frame1, frame2, num_interpolations):
    return [frame1 * (1 - alpha) + frame2 * alpha
            for alpha in np.linspace(0, 1, num_interpolations + 2)[1:-1]]


def generate_video_from_images(path_to_images: str,
                               audio_file_path: str = None,
                               image_format: str = "png",
                               desired_frame_rate: int = 60,
                               video_duration_ms: Optional[int] = 10,
                               output_video_name: str = "output_video.mp4"):
    if audio_file_path is not None:
        mp3_path = Path(path_to_images) / "audio.mp3"
        convert_to_mp3(Path(audio_file_path), mp3_path)
        if not Path(mp3_path).exists():
            raise FileNotFoundError(f"Audio file {mp3_path} does not exist")
        audio = AudioSegment.from_file(mp3_path)
        video_duration_ms = len(audio)
    else:
        mp3_path = None
    if video_duration_ms is None:
        raise ValueError("video_duration_ms must be specified if audio_file_path is not specified")

    # Read images
    images = [img for img in natsorted(os.listdir(path_to_images)) if img.endswith(image_format)]

    frame_count = len(images)
    original_frame_rate = frame_count / video_duration_ms * 1000
    num_interpolations = int(desired_frame_rate / original_frame_rate) - 1

    # Initialize video writer
    frame = cv2.imread(os.path.join(path_to_images, images[0]))
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video_path = str(Path(path_to_images) / output_video_name)
    video = cv2.VideoWriter(output_video_path, fourcc, desired_frame_rate, (width, height))

    # Write frames to the video
    for image_number in range(len(images) - 1):
        print(f"Processing image {image_number} of {len(images)}")
        frame1 = cv2.imread(os.path.join(path_to_images, images[image_number])).astype(np.float32)
        frame2 = cv2.imread(os.path.join(path_to_images, images[image_number + 1])).astype(np.float32)
        video.write(frame1.astype(np.uint8))
        interpolated_frames = simple_interpolate_frames(frame1, frame2, num_interpolations)
        for interpolated_frame in interpolated_frames:
            video.write(interpolated_frame.astype(np.uint8))

    # Don't forget the last frame
    last_frame = cv2.imread(os.path.join(path_to_images, images[-1]))
    video.write(last_frame)

    # Close video writer
    video.release()

    # After the video writing process is done
    if audio_file_path is not None and mp3_path is not None:
        add_audio_with_ffmpeg(video_path=str(output_video_path),
                              audio_path=str(mp3_path),
                              output_path=output_video_path.replace(".mp4", "_with_audio.mp4"))


def add_audio_with_ffmpeg(video_path, audio_path, output_path):
    print(f"Adding audio to video {video_path} with audio {audio_path} and saving to {output_path}")
    command = [
        'ffmpeg',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-strict', 'experimental',
        output_path
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    generate_video_from_images(path_to_images=r"C:\Users\jonma\None_data\audio_to_video\2023-12-03_12_53_46_",
                               audio_file_path=r"C:\Users\jonma\Downloads\5294aef968868b1b82e4a3627712a259.mp4",
                               image_format="png",
                               desired_frame_rate=60,
                               output_video_name="output_video.mp4")
