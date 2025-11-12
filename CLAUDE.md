# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a video transcription service that accepts video URLs from YouTube, TikTok, and Instagram, then returns a unified JSON response with metadata, full transcript text, and timestamped segments. The service uses yt-dlp for video downloading, ffmpeg for audio extraction, and OpenAI's Whisper API for transcription.

## Architecture

### Processing Pipeline

The service follows a sequential 5-stage pipeline (app/main.py:26-109):

1. **Platform Detection** (app/platform_detector.py): Validates HTTPS URLs and identifies the video platform
2. **Video Download** (app/downloader.py): Downloads video using yt-dlp with retry logic
3. **Audio Extraction** (app/audio_extractor.py): Converts video to 16kHz mono WAV using ffmpeg
4. **Metadata Normalization** (app/metadata_processor.py): Unifies metadata format across platforms
5. **Transcription** (app/transcriber.py): Sends audio to Whisper API and formats response with timestamps
   - Automatically splits audio files larger than 24 MB into chunks (app/audio_splitter.py)
   - Transcribes each chunk separately and merges results with corrected timestamps
   - Cleans up temporary chunk files after processing

Each stage has its own custom exception type for granular error handling.

### Key Components

- **app/main.py**: Flask application with single `/analyze` POST endpoint (includes error logging with traceback)
- **app/models.py**: Pydantic models for request/response validation (AnalyzeRequest, AnalyzeResponse, TimestampEntry)
- **app/transcriber.py**: Whisper API integration with automatic large file handling
- **app/audio_splitter.py**: Splits large audio files into manageable chunks for Whisper API
- **app/utils.py**: Shared utilities (trace ID generation, timestamp formatting, file cleanup)

### Data Flow

```
URL → Platform Detection → yt-dlp Download → ffmpeg Audio Extract → Whisper API → JSON Response
                                  ↓                    ↓
                            VideoMetadata          WAV file
                                  ↓                    ↓
                         NormalizedMetadata    TranscriptionResult
```

### Cleanup Strategy

All temporary files (video and audio) are cleaned up in a `finally` block (app/main.py:106-109) using `cleanup_paths()`. Files are stored in `TEMP_DIR/{trace_id}/` to prevent conflicts between concurrent requests.

## Development Commands

### Setup

```bash
# Install dependencies
pip3 install -r requirements.txt

# Configure environment (requires OPENAI_API_KEY)
cp .env.example .env
# Edit .env with your OpenAI API key

# Verify ffmpeg is installed
ffmpeg -version
```

### Running the Service

```bash
# Production mode (recommended for n8n integration)
./start_production.sh
# Uses gunicorn with 600s timeout for long transcriptions

# Development mode
python3 run.py

# Alternative methods
python3 -m app.main
export FLASK_APP=app.main:app && flask run --host=0.0.0.0 --port=8000
```

**Important for n8n users:** Use `start_production.sh` to avoid connection timeouts during long transcriptions.

### Testing

```bash
# Interactive test script (prompts for platform selection)
python3 test_api.py

# Test specific platforms
bash test_tiktok.sh
bash test_curl.sh

# Manual curl test
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

## Configuration

Environment variables (defined in .env):

- `OPENAI_API_KEY`: Required for Whisper API access
- `WHISPER_MODEL`: Whisper model to use (default: "whisper-1")
- `TEMP_DIR`: Directory for temporary files (default: "/tmp/video_api")
- `PORT`: Server port (default: 8000)

## Error Handling

The service uses custom exceptions for each processing stage:

- `InvalidUrlError`: URL validation failures (returns 400)
- `DownloadError`: yt-dlp failures (returns 500)
- `AudioExtractionError`: ffmpeg failures (returns 500)
- `TranscriptionError`: Whisper API failures (returns 500)

All error responses include a `trace_id` for debugging.

## Platform-Specific Notes

- **YouTube**: Returns full description field
- **TikTok/Instagram**: Description is omitted if empty (app/metadata_processor.py:24-26)
- All platforms use yt-dlp with retry logic and format fallback (worst/best quality)

## Audio File Size Handling

The Whisper API has a 25 MB file size limit. The service automatically handles this:

- Files under 24 MB: Sent directly to Whisper API
- Files over 24 MB: Automatically split into 10-minute chunks using ffmpeg
- Each chunk is transcribed separately
- Results are merged with corrected timestamps to maintain continuity
- Temporary chunk files are automatically cleaned up after processing

This allows transcription of videos of any length without manual intervention.

## Connection Timeouts and n8n Integration

Long transcriptions (3-10 minutes) can cause HTTP connection timeouts. Solutions:

1. **Use production server** (recommended): Run with `./start_production.sh` which uses gunicorn with 600s timeout
2. **Increase client timeout**: In n8n HTTP Request node, set timeout to 600000ms (10 minutes)
3. **Monitor progress**: Check server logs to see transcription progress while waiting

The Flask development server (`python3 run.py`) has shorter timeouts and is only suitable for testing with short videos.

## Dependencies

Critical external dependencies:

- `yt-dlp`: Video downloading with metadata extraction
- `ffmpeg`: Audio extraction and format conversion (must be in PATH)
- `openai`: Whisper API client for transcription
- `flask`: Web framework
- `pydantic`: Request/response validation

## Response Format

The API returns JSON with these fields:

- `platform`: Detected platform (youtube/tiktok/instagram)
- `url`: Canonical video URL
- `title`, `author`: Required metadata
- `description`, `language`: Optional metadata
- `duration`: Video length in seconds
- `transcript`: Full plain text transcription
- `timestamps`: Array of {time, text} objects (HH:MM:SS format)
- `trace_id`: Unique request identifier
