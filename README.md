# gtts - Google Gemini Text-to-Speech

A CLI tool for converting text documents to speech audio using Google's Gemini TTS API.

## Features

- Convert text files to WAV audio
- Support for 30 different voices
- Automatic text chunking for long documents
- Simple command-line interface

## Installation

```bash
# Clone the repository
git clone https://github.com/donaldbraman/gtts.git
cd gtts

# Install with uv
uv sync

# Or install with pip
pip install -e .
```

## Configuration

Set your Google API key:

```bash
export GOOGLE_API_KEY=your-api-key
```

Or create a `.env` file:

```
GOOGLE_API_KEY=your-api-key
```

## Usage

### Convert a text file to audio

```bash
gtts convert document.txt
gtts convert document.txt --output speech.wav --voice Puck
```

### Convert text directly

```bash
gtts speak "Hello, this is a test."
gtts speak "Hello world" --voice Zephyr
```

### List available voices

```bash
gtts voices
```

### Show configuration

```bash
gtts info
```

## Available Voices

The API supports 30 voices including: Zephyr, Puck, Charon, Kore, Fenrir, Leda, Orus, Aoede, and more.

Run `gtts voices` to see the complete list.

## Audio Output

- Format: WAV
- Sample rate: 24,000 Hz
- Channels: Mono
- Bit depth: 16-bit

## API Limits

- Context window: 32k tokens maximum per chunk
- Long documents are automatically split into chunks

## License

MIT
