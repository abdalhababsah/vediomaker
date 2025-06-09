"""
Test script to verify both voice providers are working correctly
"""

import os
import logging
from services.voice_generator import generate_voiceover

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test script
TEST_SCRIPT = "This is a test of the voice generation system. We are testing both the free Edge TTS and Eleven Labs voice providers."

def test_voice_provider(provider, voice_style):
    """Test a specific voice provider and style"""
    logger.info(f"Testing {provider} provider with {voice_style} style")
    
    try:
        # Create temp directory if it doesn't exist
        os.makedirs('temp', exist_ok=True)
        
        # Generate unique session ID for this test
        session_id = f"test_{provider}_{voice_style}"
        
        # Generate voiceover
        voice_path = generate_voiceover(
            TEST_SCRIPT, 
            'temp', 
            session_id, 
            voice_style=voice_style, 
            voice_provider=provider
        )
        
        # Check if file exists and has content
        if os.path.exists(voice_path) and os.path.getsize(voice_path) > 0:
            file_size_kb = os.path.getsize(voice_path) / 1024
            logger.info(f"✅ SUCCESS: Generated {file_size_kb:.2f} KB audio file at {voice_path}")
            return True
        else:
            logger.error(f"❌ FAILED: Audio file not generated or empty")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run tests for all voice providers and styles"""
    providers = ['free', '11']
    styles = ['normal', 'wise', 'elder', 'narrator', 'storyteller']
    
    results = {}
    
    for provider in providers:
        results[provider] = {}
        for style in styles:
            results[provider][style] = test_voice_provider(provider, style)
    
    # Print summary
    logger.info("\n--- TEST RESULTS SUMMARY ---")
    for provider in providers:
        logger.info(f"\n{provider.upper()} PROVIDER:")
        for style in styles:
            status = "✅ PASSED" if results[provider][style] else "❌ FAILED"
            logger.info(f"  {style}: {status}")
    
    # Check if Eleven Labs key is set
    if 'ELEVEN_LABS_API_KEY' not in os.environ or not os.environ['ELEVEN_LABS_API_KEY']:
        logger.warning("\n⚠️ WARNING: ELEVEN_LABS_API_KEY environment variable not set.")
        logger.warning("Eleven Labs tests may fail without a valid API key.")
        logger.warning("Set your API key with: export ELEVEN_LABS_API_KEY='your-key-here'")

if __name__ == "__main__":
    main() 