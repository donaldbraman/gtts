"""Text-to-Speech generation using Google Gemini API."""

import wave
from pathlib import Path

from google import genai
from google.genai import types
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import AVAILABLE_VOICES, settings

console = Console()


class TextToSpeech:
    """Google Gemini Text-to-Speech generator."""

    def __init__(self, voice: str = None, model: str = None):
        """Initialize TTS with voice and model settings.

        Args:
            voice: Voice name to use (default from settings)
            model: Model name to use (default from settings)
        """
        self.voice = voice or settings.default_voice
        self.model = model or settings.tts_model

        if self.voice not in AVAILABLE_VOICES:
            raise ValueError(
                f"Unknown voice: {self.voice}. Available: {', '.join(AVAILABLE_VOICES)}"
            )

        if not settings.google_api_key:
            raise ValueError(
                "No Google API key found. Set GOOGLE_API_KEY environment variable."
            )

        self.client = genai.Client(api_key=settings.google_api_key)

    def generate_audio(self, text: str) -> bytes:
        """Generate audio from text.

        Args:
            text: Text to convert to speech

        Returns:
            Raw PCM audio data (24kHz, 16-bit, mono)
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice
                        )
                    )
                ),
            ),
        )

        # Extract audio data from response (already bytes, not base64)
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        return audio_data

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks that fit within context window.

        Args:
            text: Full text to split

        Returns:
            List of text chunks
        """
        max_chars = settings.max_chunk_chars
        chunks = []

        # Split on paragraph boundaries when possible
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            # If adding this paragraph exceeds limit, save current and start new
            if len(current_chunk) + len(para) + 2 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Handle paragraphs larger than chunk size
                if len(para) > max_chars:
                    # Split on sentences
                    sentences = para.replace(". ", ".\n").split("\n")
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 > max_chars:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            current_chunk += " " + sentence if current_chunk else sentence
                else:
                    current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def generate_from_text(self, text: str, output_path: Path) -> Path:
        """Generate audio file from text, handling chunking for long texts.

        Args:
            text: Text to convert to speech
            output_path: Path to save the WAV file

        Returns:
            Path to the generated WAV file
        """
        chunks = self._chunk_text(text)
        all_audio = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Generating audio ({len(chunks)} chunks)...", total=len(chunks)
            )

            for i, chunk in enumerate(chunks):
                progress.update(task, description=f"Processing chunk {i + 1}/{len(chunks)}...")
                audio_data = self.generate_audio(chunk)
                all_audio.append(audio_data)
                progress.advance(task)

        # Combine all audio chunks
        combined_audio = b"".join(all_audio)

        # Write WAV file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(settings.channels)
            wav_file.setsampwidth(settings.sample_width)
            wav_file.setframerate(settings.sample_rate)
            wav_file.writeframes(combined_audio)

        return output_path

    def generate_from_file(self, input_path: Path, output_path: Path = None) -> Path:
        """Generate audio from a text file.

        Args:
            input_path: Path to input text file
            output_path: Path to save the WAV file (default: same name with .wav)

        Returns:
            Path to the generated WAV file
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        text = input_path.read_text()

        if output_path is None:
            output_path = settings.output_dir / f"{input_path.stem}.wav"

        return self.generate_from_text(text, output_path)
