"""Command-line interface for gtts."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import AVAILABLE_VOICES, settings
from .gdocs import GoogleDocsClient
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

    # Google OAuth status
    gdocs_client = GoogleDocsClient(
        credentials_path=settings.google_credentials_path,
        token_path=settings.google_token_path,
    )
    oauth_status = "[green]Authenticated[/green]" if gdocs_client.check_credentials() else "[yellow]Not authenticated[/yellow]"
    console.print(f"  Google OAuth: {oauth_status}")


@app.command()
def gdoc(
    url: str = typer.Argument(..., help="Google Docs URL or document ID"),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output WAV file path (default: output/<doc_title>.wav)",
    ),
    voice: str = typer.Option(
        settings.default_voice,
        "--voice",
        "-v",
        help="Voice to use for synthesis",
    ),
):
    """Convert a Google Doc to speech audio."""
    try:
        # Initialize Google Docs client
        gdocs_client = GoogleDocsClient(
            credentials_path=settings.google_credentials_path,
            token_path=settings.google_token_path,
        )

        # Get document title and content
        title = gdocs_client.get_document_title(url)
        console.print(f"[bold]Document:[/bold] {title}")

        text = gdocs_client.get_document_text(url)
        console.print(f"[dim]Fetched {len(text)} characters[/dim]")

        # Determine output path
        if output is None:
            # Sanitize title for filename
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
            safe_title = safe_title.strip()[:50]  # Limit length
            output = settings.output_dir / f"{safe_title}.wav"

        # Generate audio
        tts = TextToSpeech(voice=voice)
        result = tts.generate_from_text(text, output)
        console.print(f"[green]Audio saved to: {result}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]To set up Google OAuth:[/yellow]")
        console.print("1. Go to Google Cloud Console > APIs & Services > Credentials")
        console.print("2. Create OAuth 2.0 Client ID (Desktop application)")
        console.print("3. Download JSON and save as 'google_credentials.json'")
        console.print("4. Run 'gtts auth' to authenticate")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def auth():
    """Authenticate with Google for Google Docs access."""
    try:
        gdocs_client = GoogleDocsClient(
            credentials_path=settings.google_credentials_path,
            token_path=settings.google_token_path,
        )

        if gdocs_client.check_credentials():
            console.print("[green]Already authenticated with Google.[/green]")
            if typer.confirm("Re-authenticate?", default=False):
                # Delete existing token to force re-auth
                if settings.google_token_path.exists():
                    settings.google_token_path.unlink()
            else:
                return

        # Trigger authentication by accessing the service
        _ = gdocs_client.service
        console.print("[green]Successfully authenticated with Google![/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]To set up Google OAuth:[/yellow]")
        console.print("1. Go to Google Cloud Console > APIs & Services > Credentials")
        console.print("2. Create OAuth 2.0 Client ID (Desktop application)")
        console.print("3. Download JSON and save as 'google_credentials.json'")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
