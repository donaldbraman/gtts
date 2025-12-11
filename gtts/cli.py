"""Command-line interface for gtts."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import AVAILABLE_VOICES, settings
from .tts import TextToSpeech

app = typer.Typer(
    name="gtts",
    help="Google Gemini Text-to-Speech CLI tool",
    no_args_is_help=True,
)
console = Console()


@app.command()
def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Input text file to convert",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output WAV file path (default: output/<input_name>.wav)",
    ),
    voice: str = typer.Option(
        settings.default_voice,
        "--voice",
        "-v",
        help="Voice to use for synthesis",
    ),
):
    """Convert a text file to speech audio."""
    try:
        tts = TextToSpeech(voice=voice)
        output_path = tts.generate_from_file(input_file, output)
        console.print(f"[green]Audio saved to: {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def speak(
    text: str = typer.Argument(..., help="Text to convert to speech"),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output WAV file path (default: output/speech.wav)",
    ),
    voice: str = typer.Option(
        settings.default_voice,
        "--voice",
        "-v",
        help="Voice to use for synthesis",
    ),
):
    """Convert text directly to speech audio."""
    try:
        tts = TextToSpeech(voice=voice)
        output_path = output or settings.output_dir / "speech.wav"
        result = tts.generate_from_text(text, output_path)
        console.print(f"[green]Audio saved to: {result}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def voices():
    """List all available voices."""
    table = Table(title="Available Voices")
    table.add_column("Voice Name", style="cyan")

    for voice in AVAILABLE_VOICES:
        marker = " (default)" if voice == settings.default_voice else ""
        table.add_row(f"{voice}{marker}")

    console.print(table)


@app.command()
def info():
    """Show configuration information."""
    console.print("[bold]gtts Configuration[/bold]")
    console.print(f"  Model: {settings.tts_model}")
    console.print(f"  Default Voice: {settings.default_voice}")
    console.print(f"  Sample Rate: {settings.sample_rate} Hz")
    console.print(f"  Output Directory: {settings.output_dir}")
    console.print(f"  Max Chunk Size: {settings.max_chunk_chars} chars")

    api_key_status = "[green]Set[/green]" if settings.google_api_key else "[red]Not set[/red]"
    console.print(f"  API Key: {api_key_status}")


if __name__ == "__main__":
    app()
