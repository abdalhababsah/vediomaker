import edge_tts
import asyncio
import os
import logging
from pydub import AudioSegment
import tempfile
import re
from elevenlabs import client, VoiceSettings
from config import ELEVEN_LABS_API_KEY

logger = logging.getLogger(__name__)

# Initialize Eleven Labs client
try:
    if ELEVEN_LABS_API_KEY:
        eleven_labs = client.ElevenLabs(api_key=ELEVEN_LABS_API_KEY)
        logger.info("Eleven Labs API key configured")
    else:
        eleven_labs = None
        logger.warning("Eleven Labs API key not found. Set ELEVEN_LABS_API_KEY environment variable for '11' voice provider.")
except Exception as e:
    eleven_labs = None
    logger.error(f"Failed to initialize Eleven Labs client: {e}")

# Voice mapping for different styles with Edge TTS - OPTIMIZED FOR CONSISTENCY
VOICE_STYLES = {
    'normal': {
        'voice': 'en-US-AriaNeural',  # Professional female voice
        'rate': '+0%',
        'pitch': '+0Hz',
        'volume': '+0%'
    },
    'wise': {
        'voice': 'en-US-BrianNeural',  # Mature male voice
        'rate': '-15%',  # Slightly slower for clarity
        'pitch': '+0Hz',
        'volume': '+0%'
    },
    'elder': {
        'voice': 'en-GB-RyanNeural',  # British mature male
        'rate': '-25%',  # Slower but not too much
        'pitch': '+0Hz',
        'volume': '+0%'
    },
    'narrator': {
        'voice': 'en-US-GuyNeural',  # Changed from DavisNeural to more reliable GuyNeural
        'rate': '-5%',   # Slightly slower for narration
        'pitch': '+0Hz',  # Changed from -5Hz to +0Hz to avoid parameters issue
        'volume': '+0%'
    },
    'storyteller': {
        'voice': 'en-US-JennyNeural',  # Expressive female voice
        'rate': '+0%',
        'pitch': '+0Hz',
        'volume': '+0%'
    }
}

# Eleven Labs voice mapping with more options
ELEVEN_VOICE_STYLES = {
    'normal': {
        'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam
        'stability': 0.5,
        'similarity_boost': 0.75,
        'style': 0.0,
        'use_speaker_boost': True
    },
    'wise': {
        'voice_id': '2EiwWnXFnvU5JabPnv8n',  # Clyde 
        'stability': 0.7, 
        'similarity_boost': 0.85,
        'style': 0.3,
        'use_speaker_boost': True
    },
    'elder': {
        'voice_id': 'SOYHLrjzK2X1ezoPC6cr',  # Oswald (older British male)
        'stability': 0.8,
        'similarity_boost': 0.9,
        'style': 0.2,
        'use_speaker_boost': True
    },
    'narrator': {
        'voice_id': 'onwK4e9ZLuTAKqWW03F9',  # Daniel (deep narrator)
        'stability': 0.6,
        'similarity_boost': 0.8,
        'style': 0.4,
        'use_speaker_boost': True
    },
    'storyteller': {
        'voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella (expressive female)
        'stability': 0.4,
        'similarity_boost': 0.7,
        'style': 0.6,
        'use_speaker_boost': True
    }
}

async def generate_speech_async(text, voice, rate, pitch, volume, output_path):
    """
    Generate speech using Edge TTS asynchronously with consistent timing
    """
    try:
        # Clean text for TTS
        cleaned_text = clean_text_for_tts(text)
        if not cleaned_text:
            raise Exception("Text is empty after cleaning")
        
        logger.info(f"Generating speech with Edge TTS: voice={voice}, rate={rate}")
        logger.info(f"Text length: {len(cleaned_text)} characters")
        
        # Use plain text with Edge TTS parameters
        communicate = edge_tts.Communicate(
            text=cleaned_text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        
        # Save with consistent settings
        await communicate.save(output_path)
        
        # Verify file was created and has content
        if not os.path.exists(output_path):
            raise Exception("Audio file was not created")
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise Exception("Generated audio file is empty")
        
        # Get actual duration for logging
        try:
            audio = AudioSegment.from_file(output_path)
            actual_duration = len(audio) / 1000.0
            logger.info(f"Edge TTS audio saved: {output_path} ({file_size} bytes, {actual_duration:.2f}s)")
        except:
            logger.info(f"Edge TTS audio saved: {output_path} ({file_size} bytes)")
        
        return True
        
    except Exception as e:
        logger.error(f"Edge TTS generation failed: {e}")
        return False

def generate_elevenlabs_speech(text, voice_config, output_path):
    """Generate speech using Eleven Labs with consistent settings"""
    try:
        if not eleven_labs:
            raise Exception("Eleven Labs client not initialized")
        
        # Clean text for TTS
        cleaned_text = clean_text_for_tts(text)
        if not cleaned_text:
            raise Exception("Text is empty after cleaning")
        
        # Get voice settings
        voice_id = voice_config['voice_id']
        stability = voice_config.get('stability', 0.5)
        similarity_boost = voice_config.get('similarity_boost', 0.75)
        style = voice_config.get('style', 0.0)
        use_speaker_boost = voice_config.get('use_speaker_boost', True)
        
        # Configure voice settings for consistency
        voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost
        )
        
        # Generate audio
        logger.info(f"Generating speech with Eleven Labs: voice_id={voice_id}, stability={stability}")
        logger.info(f"Text length: {len(cleaned_text)} characters")
        
        # Generate audio using the text_to_speech method
        audio = eleven_labs.text_to_speech.convert(
            text=cleaned_text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings
        )
        
        # Save to file
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        # Verify file was created and has content
        if not os.path.exists(output_path):
            raise Exception("Audio file was not created")
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise Exception("Generated audio file is empty")
        
        # Get actual duration for logging
        try:
            audio_seg = AudioSegment.from_file(output_path)
            actual_duration = len(audio_seg) / 1000.0
            logger.info(f"Eleven Labs audio generated: {file_size} bytes, {actual_duration:.2f}s")
        except:
            logger.info(f"Eleven Labs audio generated: {file_size} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"Eleven Labs speech generation failed: {e}")
        return False

def clean_text_for_tts(text):
    """Clean and prepare text for TTS processing with consistent formatting"""
    if not text:
        return ""
    
    # Replace problematic characters
    text = text.replace('\u2014', ' -- ')  # Em dash
    text = text.replace('\u2013', ' - ')   # En dash
    text = text.replace('\u2018', "'")     # Left single quote
    text = text.replace('\u2019', "'")     # Right single quote
    text = text.replace('\u201c', '"')     # Left double quote
    text = text.replace('\u201d', '"')     # Right double quote
    text = text.replace('\u2026', '...')   # Ellipsis
    text = text.replace('\u00a0', ' ')     # Non-breaking space
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Ensure proper sentence endings for natural pauses
    text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
    
    # Add slight pauses for commas (helps with timing)
    text = re.sub(r',\s*', r', ', text)
    
    # Ensure text ends with punctuation for proper closure
    if text and not text[-1] in '.!?':
        text += '.'
    
    return text.strip()

def generate_voiceover(script, output_folder, session_id, language='en', slow=False, voice_style='normal', voice_provider='free'):
    """Generate voiceover from text script with consistent timing"""
    try:
        logger.info(f"Generating voiceover for session {session_id}")
        logger.info(f"Script length: {len(script)} characters")
        logger.info(f"Voice style: {voice_style}")
        logger.info(f"Voice provider: {voice_provider}")
        
        # Validate inputs
        if not script or not script.strip():
            raise Exception("Script is empty or contains only whitespace")
        
        if not output_folder:
            raise Exception("Output folder not specified")
        
        if not session_id:
            raise Exception("Session ID not specified")
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Clean script for consistent processing
        cleaned_script = clean_text_for_tts(script)
        if not cleaned_script:
            raise Exception("Script is empty after cleaning")
        
        # Log estimated duration
        estimated_duration = estimate_audio_duration(cleaned_script, voice_style, voice_provider)
        logger.info(f"Estimated audio duration: {estimated_duration:.2f}s")
        
        # Generate output path - use WAV first for better compatibility
        audio_filename = f"{session_id}_voiceover.wav"
        audio_path = os.path.join(output_folder, audio_filename)
        
        # Try primary voice provider
        success = False
        
        if voice_provider == '11':
            success = try_elevenlabs_generation(cleaned_script, voice_style, audio_path)
            
            # Fallback to Edge TTS if Eleven Labs fails
            if not success:
                logger.warning("Eleven Labs failed, falling back to Edge TTS")
                success = try_edgetts_generation(cleaned_script, voice_style, audio_path)
        else:
            success = try_edgetts_generation(cleaned_script, voice_style, audio_path)
            
            # Fallback to Eleven Labs if available and Edge TTS fails
            if not success and eleven_labs:
                logger.warning("Edge TTS failed, falling back to Eleven Labs")
                success = try_elevenlabs_generation(cleaned_script, voice_style, audio_path)
        
        if not success:
            raise Exception("All voice generation methods failed")
        
        # Post-process audio file for consistency
        final_audio_path = post_process_audio_enhanced(audio_path, output_folder, session_id, voice_style)
        
        logger.info(f"Voiceover generated successfully: {final_audio_path}")
        logger.info(f"Final file size: {os.path.getsize(final_audio_path)} bytes")
        
        return final_audio_path
            
    except Exception as e:
        logger.error(f"Error generating voiceover: {str(e)}")
        raise Exception(f"Failed to generate voiceover: {str(e)}")

def try_elevenlabs_generation(script, voice_style, output_path):
    """Try to generate speech using Eleven Labs"""
    try:
        if not eleven_labs:
            logger.warning("Eleven Labs not available")
            return False
        
        # Get voice configuration
        if voice_style not in ELEVEN_VOICE_STYLES:
            logger.warning(f"Unknown voice style '{voice_style}' for Eleven Labs, using 'normal'")
            voice_style = 'normal'
            
        voice_config = ELEVEN_VOICE_STYLES[voice_style]
        
        # Generate speech using Eleven Labs
        success = generate_elevenlabs_speech(script, voice_config, output_path)
        
        if success:
            logger.info("✅ Eleven Labs generation successful")
            return True
        else:
            logger.warning("❌ Eleven Labs generation failed")
            return False
        
    except Exception as e:
        logger.error(f"Eleven Labs generation attempt failed: {e}")
        return False

def try_edgetts_generation(script, voice_style, output_path):
    """Try to generate speech using Edge TTS"""
    try:
        # Get voice configuration
        if voice_style not in VOICE_STYLES:
            logger.warning(f"Unknown voice style '{voice_style}' for Edge TTS, using 'normal'")
            voice_style = 'normal'
            
        voice_config = VOICE_STYLES[voice_style]
        logger.info(f"Using Edge TTS voice: {voice_config['voice']}, rate: {voice_config['rate']}")
        
        # Generate speech using Edge TTS
        success = asyncio.run(
            generate_speech_async(
                script,
                voice_config['voice'],
                voice_config['rate'],
                voice_config['pitch'],
                voice_config['volume'],
                output_path
            )
        )
        
        if success:
            logger.info("✅ Edge TTS generation successful")
            return True
        else:
            logger.warning("❌ Edge TTS generation failed")
            return False
        
    except Exception as e:
        logger.error(f"Edge TTS generation attempt failed: {e}")
        return False

def post_process_audio_enhanced(input_path, output_folder, session_id, voice_style):
    """Enhanced post-processing for consistent audio timing"""
    try:
        logger.info("Post-processing audio file for optimal timing")
        
        # Load audio file
        audio = AudioSegment.from_file(input_path)
        original_duration = len(audio) / 1000.0
        logger.info(f"Original audio duration: {original_duration:.2f}s")
        
        # Normalize audio levels for consistency
        audio = audio.normalize()
        
        # Apply consistent fade in/out to prevent clicks
        fade_duration = 50  # milliseconds
        audio = audio.fade_in(fade_duration).fade_out(fade_duration)
        
        # Remove excessive silence at start and end for better sync
        # Detect leading silence
        silence_thresh = -40  # dB
        min_silence_len = 100  # ms
        
        # Trim silence at start
        start_trim = 0
        for i in range(0, len(audio), 10):  # Check every 10ms
            if audio[i:i+min_silence_len].dBFS > silence_thresh:
                start_trim = max(0, i - 50)  # Keep 50ms buffer
                break
        
        # Trim silence at end
        end_trim = len(audio)
        for i in range(len(audio) - min_silence_len, 0, -10):
            if audio[i:i+min_silence_len].dBFS > silence_thresh:
                end_trim = min(len(audio), i + min_silence_len + 50)  # Keep 50ms buffer
                break
        
        # Apply trimming
        if start_trim > 0 or end_trim < len(audio):
            audio = audio[start_trim:end_trim]
            new_duration = len(audio) / 1000.0
            logger.info(f"Trimmed audio: removed {start_trim}ms from start, "
                       f"{len(audio) - end_trim}ms from end. New duration: {new_duration:.2f}s")
        
        # Convert to MP3 for consistency and smaller file size
        mp3_filename = f"{session_id}_voiceover.mp3"
        mp3_path = os.path.join(output_folder, mp3_filename)
        
        # Export as high-quality MP3 with consistent settings
        audio.export(
            mp3_path, 
            format="mp3", 
            bitrate="128k",
            parameters=[
                "-q:a", "2",  # High quality
                "-ar", "44100",  # Standard sample rate
            ]
        )
        
        # Verify the exported file
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            # Remove original WAV file
            try:
                os.remove(input_path)
                logger.info("Audio converted to MP3 and original WAV removed")
            except:
                logger.warning("Could not remove original WAV file")
            
            # Log final duration
            final_audio = AudioSegment.from_file(mp3_path)
            final_duration = len(final_audio) / 1000.0
            logger.info(f"Final audio duration: {final_duration:.2f}s")
            
            return mp3_path
        else:
            logger.warning("MP3 conversion failed, using original WAV file")
            return input_path
        
    except Exception as e:
        logger.warning(f"Audio post-processing failed: {e}. Using original file.")
        return input_path

def get_available_voices():
    """Get list of available voices for both providers"""
    available_voices = {
        'free': {
            'normal': {
                'name': 'Professional Voice (Aria)',
                'voice': 'en-US-AriaNeural',
                'description': 'Clear, professional female voice',
                'language': 'English (US)'
            },
            'wise': {
                'name': 'Wise Narrator (Brian)',
                'voice': 'en-US-BrianNeural', 
                'description': 'Mature, authoritative male voice',
                'language': 'English (US)'
            },
            'elder': {
                'name': 'Elder Sage (Ryan)',
                'voice': 'en-GB-RyanNeural',
                'description': 'Distinguished British mature male voice',
                'language': 'English (UK)'
            },
            'narrator': {
                'name': 'Deep Narrator (Davis)',
                'voice': 'en-US-DavisNeural',
                'description': 'Deep, storytelling male voice',
                'language': 'English (US)'
            },
            'storyteller': {
                'name': 'Expressive Storyteller (Jenny)',
                'voice': 'en-US-JennyNeural',
                'description': 'Expressive, engaging female voice',
                'language': 'English (US)'
            }
        },
        '11': {
            'normal': {
                'name': 'Adam',
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'description': 'Clear, professional male voice',
                'language': 'English'
            },
            'wise': {
                'name': 'Clyde',
                'voice_id': '2EiwWnXFnvU5JabPnv8n',
                'description': 'Mature, authoritative male voice',
                'language': 'English'
            },
            'elder': {
                'name': 'Oswald',
                'voice_id': 'SOYHLrjzK2X1ezoPC6cr',
                'description': 'Distinguished British mature male voice',
                'language': 'English (British)'
            },
            'narrator': {
                'name': 'Daniel',
                'voice_id': 'onwK4e9ZLuTAKqWW03F9',
                'description': 'Deep, narrative male voice',
                'language': 'English (British)'
            },
            'storyteller': {
                'name': 'Bella',
                'voice_id': 'EXAVITQu4vr4xnSDxMaL',
                'description': 'Expressive, storytelling female voice',
                'language': 'English'
            }
        }
    }
    
    return available_voices

def validate_voice_style(voice_style, voice_provider='free'):
    """Validate if the voice style is supported"""
    voice_style_lower = voice_style.lower()
    
    if voice_provider == '11':
        return voice_style_lower in ELEVEN_VOICE_STYLES
    else:
        return voice_style_lower in VOICE_STYLES

def estimate_audio_duration(text, voice_style='normal', voice_provider='free'):
    """Estimate the duration of the generated audio more accurately"""
    if not text:
        return 0.0
    
    # Count words and characters
    word_count = len(text.split())
    char_count = len(text)
    
    # Base WPM for different styles and providers
    if voice_provider == '11':
        wpm_map = {
            'normal': 150,
            'wise': 130,
            'elder': 110,
            'narrator': 140,
            'storyteller': 160
        }
    else:
        # Edge TTS rates adjusted for actual performance
        wpm_map = {
            'normal': 150,
            'wise': 125,   # -15% rate
            'elder': 110,   # -25% rate
            'narrator': 140, # -5% rate
            'storyteller': 155
        }
    
    base_wpm = wpm_map.get(voice_style, 150)
    
    # Calculate base duration
    duration_minutes = word_count / base_wpm
    base_duration = duration_minutes * 60
    
    # Add time for punctuation pauses
    period_count = text.count('.') + text.count('!') + text.count('?')
    comma_count = text.count(',')
    semicolon_count = text.count(';') + text.count(':')
    
    pause_time = (period_count * 0.3) + (comma_count * 0.15) + (semicolon_count * 0.2)
    
    # Add a small buffer for processing
    total_duration = base_duration + pause_time + 0.5
    
    return round(total_duration, 2)

def test_voice_providers():
    """Test both voice providers"""
    results = {
        'edge_tts': {'available': False, 'error': None},
        'eleven_labs': {'available': False, 'error': None}
    }
    
    # Test Edge TTS
    try:
        test_text = "Testing Edge TTS voice generation."
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            success = asyncio.run(
                generate_speech_async(
                    test_text,
                    'en-US-AriaNeural',
                    '+0%',
                    '+0Hz',
                    '+0%',
                    tmp_file.name
                )
            )
            if success and os.path.exists(tmp_file.name) and os.path.getsize(tmp_file.name) > 0:
                results['edge_tts']['available'] = True
                logger.info("✅ Edge TTS test successful")
            else:
                results['edge_tts']['error'] = "Test generation failed"
            
            # Clean up
            try:
                os.unlink(tmp_file.name)
            except:
                pass
                
    except Exception as e:
        results['edge_tts']['error'] = str(e)
        logger.warning(f"❌ Edge TTS test failed: {e}")
    
    # Test Eleven Labs
    if eleven_labs:
        try:
            test_text = "Testing Eleven Labs voice generation."
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                voice_config = ELEVEN_VOICE_STYLES['normal']
                success = generate_elevenlabs_speech(test_text, voice_config, tmp_file.name)
                
                if success and os.path.exists(tmp_file.name) and os.path.getsize(tmp_file.name) > 0:
                    results['eleven_labs']['available'] = True
                    logger.info("✅ Eleven Labs test successful")
                else:
                    results['eleven_labs']['error'] = "Test generation failed"
                
                # Clean up
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
                    
        except Exception as e:
            results['eleven_labs']['error'] = str(e)
            logger.warning(f"❌ Eleven Labs test failed: {e}")
    else:
        results['eleven_labs']['error'] = "Client not initialized (missing API key)"
    
    return results

def get_recommended_voice_style(text_content):
    """Analyze text content and recommend an appropriate voice style"""
    if not text_content:
        return 'normal'
    
    text_lower = text_content.lower()
    
    # Check for storytelling indicators
    story_keywords = ['once upon a time', 'story', 'tale', 'adventure', 'character', 'plot']
    if any(keyword in text_lower for keyword in story_keywords):
        return 'storyteller'
    
    # Check for wisdom/educational content
    wisdom_keywords = ['wisdom', 'learn', 'important', 'remember', 'understand', 'knowledge']
    if any(keyword in text_lower for keyword in wisdom_keywords):
        return 'wise'
    
    # Check for formal/professional content
    formal_keywords = ['analysis', 'report', 'data', 'research', 'study', 'findings']
    if any(keyword in text_lower for keyword in formal_keywords):
        return 'normal'
    
    # Check for narrative content
    narrative_keywords = ['narrator', 'narrative', 'documentary', 'explanation', 'describes']
    if any(keyword in text_lower for keyword in narrative_keywords):
        return 'narrator'
    
    # Default to normal for general content
    return 'normal'