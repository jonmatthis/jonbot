import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from natsort import natsorted
from pydub import AudioSegment


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
        if not Path(audio_file_path).exists():
            raise FileNotFoundError(f"Audio file {audio_file_path} does not exist")
        audio = AudioSegment.from_file(audio_file_path)
        video_duration_ms = len(audio)

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

    # # Add audio to video
    # print("Adding audio to video")
    # if audio_file_path is not None:
    #     video_clip = VideoFileClip(output_video_path)
    #     audio_clip = AudioFileClip(audio_file_path)
    #     final_clip = video_clip.set_audio(audio_clip)
    #     final_clip.write_videofile(output_video_path, codec='libx264', audio_codec='aac')


if __name__ == "__main__":
    generate_video_from_images(path_to_images=r"C:\Users\jonma\None_data\audio_to_video\2023-12-03_10_37_00_",
                               audio_file_path=r"C:\Users\jonma\Downloads\voice-message(7).ogg",
                               image_format="png",
                               desired_frame_rate=60,
                               output_video_name="output_video.mp4")
