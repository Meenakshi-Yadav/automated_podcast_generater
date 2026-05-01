# automated_podcast_generater
Python project that extracts the latest Aeon essay and converts it into an AI‑generated podcast.
This repository contains `podcast_builder.py`, a script that fetches AEON essays, generates a CAT-prep podcast script using a local Ollama model, and converts the final script into speech using the ElevenLabs API.

## Overview

- `podcast_builder.py`: Main pipeline for essay scraping, script generation, and TTS conversion.
- `script.txt`: Output file containing the generated podcast script.

## ElevenLabs API Usage

The ElevenLabs API is used to convert the generated podcast script into an MP3 file. The script uses the official `elevenlabs` Python client and the `_text_to_speech.convert()` endpoint to generate audio.

### Required configuration

1. Create a `.env` file in the project directory.
2. Add your ElevenLabs API key:

```env
ELEVENLABS_API_KEY=your_api_key_here
```

3. Install dependencies:

```powershell
pip install requests beautifulsoup4 python-dotenv elevenlabs
```

### How the TTS flow works

- `script_to_mp3(script, output_filename)`: converts the final text script into speech.
- For long scripts, the text is split into smaller chunks by `split_text()` to avoid hitting text size limits.
- Each chunk is sent to ElevenLabs with:
  - `voice_id="JBFqnCBsd6RMkjVDRZzb"`
  - `model_id="eleven_v3"`
  - `output_format="mp3_44100_128"`
- The resulting MP3 chunks are saved temporarily and merged by binary concatenation into one output file.

### Important notes

- The script uses `elevenlabs._text_to_speech.convert()`. If the ElevenLabs SDK is updated, verify the client interface and update the call accordingly.
- The current chunk size target is `4500` characters. This can be adjusted in `split_text()` if your scripts are longer or shorter.
- The merged MP3 file is produced by concatenating bytes from each chunk file. This works for simple MP3 outputs, but if you need a more robust merge, consider using an audio library like `pydub`.

## Running the script

1. Ensure `.env` is present with `ELEVENLABS_API_KEY`.
2. Run the script from the `aeon_podcast` folder:

```powershell
python podcast_builder.py
```

3. When prompted, paste an AEON essay URL. The script will:
   - fetch the essay content
   - generate a podcast script
   - convert the script to speech
   - save the MP3 file with a title-based filename

## Customization

- Change `voice_id` or `model_id` inside `script_to_mp3()` to use different ElevenLabs voices or models.
- Update the prompt in `generate_script()` to adjust podcast structure, vocabulary flags, or question style.
- If you want to process the latest AEON essay automatically, you can reuse `get_latest_aeon_essay()` by modifying `main()`.
