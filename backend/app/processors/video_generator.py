"""
Video Generator - Create animated video from PDF pages
"""
from moviepy.editor import (
    ImageClip,
    concatenate_videoclips,
    CompositeVideoClip,
    TextClip,
    AudioFileClip
)
from gtts import gTTS
from pathlib import Path
from typing import Dict, Callable, Optional
import os


class VideoGenerator:
    def __init__(self):
        self.fps = 24
        self.duration_per_page = 3  # seconds
        self.transition_duration = 0.5  # seconds
        self.video_size = (1920, 1080)  # 1080p

    def generate(
        self,
        pdf_data: Dict,
        output_path: str,
        temp_dir: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ):
        """
        Generate video from PDF data

        Args:
            pdf_data: Dict with pages data from PDFProcessor
            output_path: Path to save the output video
            temp_dir: Temporary directory for intermediate files
            progress_callback: Optional callback for progress updates
        """
        pages = pdf_data["pages"]
        num_pages = len(pages)

        if num_pages == 0:
            raise ValueError("No pages to process")

        # Step 1: Generate narration audio (if there's text)
        audio_path = None
        all_text = " ".join([page["text"] for page in pages if page["text"]])

        if all_text:
            audio_path = Path(temp_dir) / "narration.mp3"
            print("Generating narration audio...")
            self._generate_audio(all_text[:1000], str(audio_path))  # Limit text length

            if progress_callback:
                progress_callback(0.2)

        # Step 2: Create video clips from page images
        print("Creating video clips from pages...")
        clips = []

        for idx, page in enumerate(pages):
            image_path = page["image_path"]

            if not os.path.exists(image_path):
                print(f"Warning: Image not found: {image_path}")
                continue

            # Create image clip
            clip = ImageClip(image_path).set_duration(self.duration_per_page)

            # Resize to fit video dimensions
            clip = clip.resize(height=self.video_size[1])

            # Add fade in/out transitions
            if idx > 0:
                clip = clip.crossfadein(self.transition_duration)

            if idx < num_pages - 1:
                clip = clip.crossfadeout(self.transition_duration)

            clips.append(clip)

            if progress_callback:
                progress_callback(0.2 + (0.5 * (idx + 1) / num_pages))

        # Step 3: Concatenate clips
        print("Concatenating clips...")
        final_video = concatenate_videoclips(clips, method="compose")

        # Step 4: Add audio if available
        if audio_path and os.path.exists(audio_path):
            print("Adding narration...")
            audio = AudioFileClip(str(audio_path))

            # Adjust video duration to match audio if needed
            if audio.duration > final_video.duration:
                # Extend video duration by slowing down clips proportionally
                scale_factor = audio.duration / final_video.duration
                final_video = final_video.fx(lambda clip: clip.set_duration(clip.duration * scale_factor))

            final_video = final_video.set_audio(audio)

        if progress_callback:
            progress_callback(0.8)

        # Step 5: Render final video
        print("Rendering final video...")
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=f"{temp_dir}/temp-audio.m4a",
            remove_temp=True,
            verbose=False,
            logger=None
        )

        # Cleanup
        final_video.close()
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

        if progress_callback:
            progress_callback(1.0)

        print("Video generation complete!")

    def _generate_audio(self, text: str, output_path: str):
        """Generate TTS audio from text"""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
        except Exception as e:
            print(f"Warning: Could not generate audio: {e}")
            # Continue without audio
