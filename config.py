import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Eleven Labs API configuration
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY', '')

# Video processing configuration
DEFAULT_VIDEO_WIDTH = 1920
DEFAULT_VIDEO_HEIGHT = 1080
DEFAULT_VIDEO_FPS = 24

# Audio processing configuration
DEFAULT_AUDIO_BITRATE = '128k'
DEFAULT_AUDIO_FORMAT = 'mp3'

# Transcript processing configuration
MIN_SEGMENT_DURATION = 0.1  # Minimum segment duration in seconds
MAX_SEGMENT_DURATION = 10.0  # Maximum segment duration in seconds
DEFAULT_WORDS_PER_MINUTE = 150  # For duration estimation

# Subtitle configuration
MAX_SUBTITLE_CHARS_PER_LINE = 60
MAX_SUBTITLE_LINES = 2
SUBTITLE_FONT_SIZE = 48
SUBTITLE_OUTLINE_WIDTH = 3

# Voice provider configuration
DEFAULT_VOICE_PROVIDER = 'free'  # 'free' for Edge TTS, '11' for Eleven Labs
DEFAULT_VOICE_STYLE = 'normal'

# File paths and directories
TEMP_DIR = os.getenv('TEMP_DIR', 'temp')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
ASSETS_DIR = os.getenv('ASSETS_DIR', 'assets')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# API rate limiting (for Eleven Labs)
MAX_REQUESTS_PER_MINUTE = 20
REQUEST_TIMEOUT = 30  # seconds

# Error handling configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds between retries

# Validation settings
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.aac', '.ogg']
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv']

# Quality settings
AUDIO_QUALITY = 'high'  # 'low', 'medium', 'high'
VIDEO_QUALITY = 'medium'  # 'low', 'medium', 'high'

# Feature flags
ENABLE_WHISPER_TRANSCRIPTION = True
ENABLE_SUBTITLE_GENERATION = True
ENABLE_AUDIO_NORMALIZATION = True
ENABLE_VIDEO_PREVIEW = True

# Cache settings
ENABLE_CACHING = True
CACHE_DURATION = 3600  # 1 hour in seconds

def get_quality_settings(quality='medium'):
    """
    Get quality settings for different quality levels
    
    Args:
        quality (str): Quality level ('low', 'medium', 'high')
        
    Returns:
        dict: Quality settings
    """
    settings = {
        'low': {
            'video_bitrate': '500k',
            'audio_bitrate': '64k',
            'video_crf': 28,
            'audio_quality': 5
        },
        'medium': {
            'video_bitrate': '1000k',
            'audio_bitrate': '128k',
            'video_crf': 23,
            'audio_quality': 2
        },
        'high': {
            'video_bitrate': '2000k',
            'audio_bitrate': '192k',
            'video_crf': 18,
            'audio_quality': 0
        }
    }
    
    return settings.get(quality, settings['medium'])

def setup_logging():
    """
    Setup logging configuration
    """
    import logging
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    
    return logging.getLogger(__name__)

def ensure_directories():
    """
    Ensure all required directories exist
    """
    directories = [TEMP_DIR, OUTPUT_DIR, ASSETS_DIR]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Initialize logging and directories when module is imported
logger = setup_logging()
ensure_directories()

logger.info("Configuration loaded successfully")
if ELEVEN_LABS_API_KEY:
    logger.info("Eleven Labs API key configured")
else:
    logger.warning("Eleven Labs API key not found. Set ELEVEN_LABS_API_KEY environment variable for premium voice features.")