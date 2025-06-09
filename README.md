# Video Maker API

A Flask-based API for generating videos with voiceovers, subtitles, and background images.

## Features

- Generate voiceovers from text with different voice styles
- Create videos with subtitles and background images
- Support for both free (Edge TTS) and premium (Eleven Labs) voice providers
- Customizable voice styles: normal, wise, elder

## Setup

1. Clone the repository
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install FFmpeg if not already installed
4. For Eleven Labs voice provider, set your API key:
   ```
   export ELEVEN_LABS_API_KEY="your-api-key-here"
   ```
5. Run the application:
   ```
   python app.py
   ```

## API Endpoints

### Create Video

`POST /create-video`

Creates a video with voiceover and subtitles.

#### Request

Form data:
- `script` (required): Text script for voiceover
- `background_image` (required): Background image file
- `voice_style` (optional): Voice style - 'normal', 'wise', 'elder' (default: 'elder')
- `voice_provider` (optional): Voice provider - 'free' or '11' (default: 'free')

#### Response

```json
{
    "success": true,
    "message": "Video created successfully",
    "session_id": "unique-session-id",
    "video_path": "path/to/video.mp4",
    "download_url": "/download/unique-session-id",
    "voice_provider": "free"
}
```

### Download Video

`GET /download/{session_id}`

Downloads the generated video.

### List Videos

`GET /list-videos`

Lists all generated videos.

## Voice Providers

### Free (Edge TTS)

Uses Microsoft Edge TTS for voice generation. No API key required.

Voices:
- `normal`: Professional female voice (en-US-AriaNeural)
- `wise`: Mature male voice with slower rate (en-US-BrianNeural)
- `elder`: British mature male voice with very slow rate (en-GB-RyanNeural)

### Premium (Eleven Labs)

Uses Eleven Labs for more natural-sounding voices. Requires API key.

Voices:
- `normal`: Clear, professional male voice (Adam)
- `wise`: Mature, authoritative male voice (Clyde)
- `elder`: Distinguished British mature male voice (Oswald)

## Example Usage

### Using cURL

```bash
curl -X POST -F "script=This is a test script." -F "background_image=@/path/to/image.jpg" -F "voice_style=elder" -F "voice_provider=free" http://localhost:5001/create-video
```

### Using Python

```python
import requests

url = "http://localhost:5001/create-video"
files = {"background_image": open("/path/to/image.jpg", "rb")}
data = {
    "script": "This is a test script.",
    "voice_style": "elder",
    "voice_provider": "11"  # Use Eleven Labs
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## Configuration

Edit `config.py` to change default settings:

```python
# Default configuration
DEFAULT_VOICE_PROVIDER = "free"  # 'free' or '11'
DEFAULT_VOICE_STYLE = "elder"
```

## Project Structure

```
vediomaker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── services/             # Core business logic
│   ├── __init__.py
│   ├── voice_generator.py    # Text-to-speech service
│   ├── transcript_generator.py  # Speech-to-text service
│   └── video_creator.py      # Video creation service
├── utils/                # Utility functions
│   ├── __init__.py
│   └── file_handler.py       # File management utilities
├── uploads/              # Uploaded files (created at runtime)
├── temp/                 # Temporary files (created at runtime)
└── outputs/              # Generated videos (created at runtime)
```

## Configuration

The application creates the following directories automatically:
- `uploads/` - Stores uploaded background images
- `temp/` - Temporary files during processing
- `outputs/` - Final generated videos

## Error Handling

The API includes comprehensive error handling:
- File validation (type, size)
- Audio generation errors
- Video processing failures
- Network connectivity issues
- Proper HTTP status codes and error messages

## Logging

The application logs all operations including:
- Request processing
- File operations
- Service execution
- Error tracking

## Performance Considerations

- **Processing Time**: Video creation time depends on script length
- **File Sizes**: Generated videos are optimized for web delivery
- **Concurrent Requests**: Each request gets a unique session ID
- **Cleanup**: Temporary files are automatically cleaned up

## Supported Languages

The gTTS service supports multiple languages. Default is English ('en').
Supported languages include:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- And many more...

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure FFmpeg is installed and accessible in PATH
   - On macOS: `brew install ffmpeg`
   - On Linux: `sudo apt install ffmpeg`

2. **Internet connection required**
   - gTTS requires internet for text-to-speech generation
   - Speech recognition also requires internet connectivity

3. **Large file processing**
   - Processing time increases with script length
   - Consider breaking very long scripts into segments

4. **Memory usage**
   - Video processing can be memory-intensive
   - Monitor system resources for large videos

### Logs

Check application logs for detailed error information:
```bash
python3 app.py
```

## Development

To extend the application:

1. **Add new services** in the `services/` directory
2. **Add utilities** in the `utils/` directory
3. **Modify API endpoints** in `app.py`
4. **Update requirements** in `requirements.txt`

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues and enhancement requests! 