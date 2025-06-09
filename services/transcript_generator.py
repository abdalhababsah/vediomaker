import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
import tempfile
import logging
import re

logger = logging.getLogger(__name__)

def generate_transcript(audio_path):
    """Generate transcript with timing information from audio file"""
    try:
        logger.info(f"Generating transcript from: {audio_path}")
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Get audio duration
        audio_duration = get_audio_duration(audio_path)
        logger.info(f"Audio duration: {audio_duration} seconds")
        
        # Convert MP3 to WAV if necessary
        wav_path = convert_to_wav(audio_path)
        
        # Split audio on silence for better word timing
        segments = split_audio_on_silence(wav_path)
        
        transcript_data = {
            "full_text": "",
            "segments": [],
            "duration": audio_duration,
            "word_count": 0
        }
        
        current_time = 0.0
        
        for i, segment in enumerate(segments):
            try:
                # Save segment temporarily
                segment_path = f"{wav_path}_segment_{i}.wav"
                segment.export(segment_path, format="wav")
                
                # Recognize speech in segment
                with sr.AudioFile(segment_path) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                
                # Calculate segment timing
                segment_duration = len(segment) / 1000.0
                
                segment_info = {
                    "text": text,
                    "start_time": round(current_time, 2),
                    "end_time": round(current_time + segment_duration, 2),
                    "duration": round(segment_duration, 2)
                }
                
                transcript_data["segments"].append(segment_info)
                transcript_data["full_text"] += text + " "
                
                current_time += segment_duration
                
                # Clean up segment file
                if os.path.exists(segment_path):
                    os.remove(segment_path)
                    
                logger.info(f"Segment {i+1}: '{text}' ({segment_duration:.2f}s)")
                
            except sr.UnknownValueError:
                logger.warning(f"Could not understand segment {i+1}")
                segment_duration = len(segment) / 1000.0
                current_time += segment_duration
                
            except sr.RequestError as e:
                logger.error(f"Error with speech recognition service: {e}")
                segment_duration = len(segment) / 1000.0
                current_time += segment_duration
        
        # Clean up
        transcript_data["full_text"] = transcript_data["full_text"].strip()
        transcript_data["word_count"] = len(transcript_data["full_text"].split())
        
        # Clean up WAV file if it was converted
        if wav_path != audio_path and os.path.exists(wav_path):
            os.remove(wav_path)
        
        logger.info(f"Transcript generated: {transcript_data['word_count']} words, {len(transcript_data['segments'])} segments")
        
        return transcript_data
        
    except Exception as e:
        logger.error(f"Error generating transcript: {str(e)}")
        return create_fallback_transcript(audio_path)

def convert_to_wav(audio_path):
    """Convert audio file to WAV format if necessary"""
    if audio_path.lower().endswith('.wav'):
        return audio_path
    
    try:
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
        audio.export(wav_path, format="wav")
        logger.info(f"Converted {audio_path} to {wav_path}")
        return wav_path
    except Exception as e:
        logger.error(f"Error converting to WAV: {str(e)}")
        return audio_path

def split_audio_on_silence(audio_path, min_silence_len=500, silence_thresh=-40):
    """Split audio file on silence for better speech recognition"""
    try:
        audio = AudioSegment.from_wav(audio_path)
        
        segments = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=200
        )
        
        segments = [seg for seg in segments if len(seg) > 300]
        
        if not segments:
            segments = [audio]
        
        logger.info(f"Split audio into {len(segments)} segments")
        return segments
        
    except Exception as e:
        logger.error(f"Error splitting audio: {str(e)}")
        audio = AudioSegment.from_file(audio_path)
        return [audio]

def get_audio_duration(audio_path):
    """Get the duration of an audio file in seconds"""
    try:
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio) / 1000.0
        return round(duration, 2)
    except Exception as e:
        logger.error(f"Error getting audio duration: {str(e)}")
        return 0.0

def generate_transcript_from_script_and_audio(script, audio_path):
    """
    FIXED: Generate transcript timing that MATCHES the actual voice generation
    """
    try:
        logger.info(f"Generating ACCURATE transcript timing from script and audio: {audio_path}")
        
        # Get ACTUAL audio duration from the generated file
        audio_duration = get_audio_duration(audio_path)
        logger.info(f"ACTUAL audio duration: {audio_duration} seconds")
        
        if audio_duration <= 0:
            raise Exception("Invalid audio duration")
        
        # Clean script
        cleaned_script = script.strip()
        if not cleaned_script:
            raise Exception("Script is empty")
        
        # Split script into segments for subtitles with improved timing
        segments = split_script_into_natural_segments(cleaned_script)
        
        transcript_data = {
            "full_text": cleaned_script,
            "segments": [],
            "duration": audio_duration,
            "word_count": len(cleaned_script.split())
        }
        
        # IMPROVED TIMING CALCULATION
        if len(segments) > 0:
            # Calculate character-based timing with speech rate adjustment
            total_chars = sum(len(segment) for segment in segments)
            
            # Average speaking rate: 150-160 words per minute
            # Approximate 5 characters per word including spaces
            # So roughly 750-800 characters per minute
            chars_per_second = 13.0  # Average for natural speech
            
            # Adjust for actual audio duration
            actual_chars_per_second = total_chars / audio_duration
            
            # Use a weighted average between expected and actual rates
            # This helps handle both fast and slow speech
            effective_chars_per_second = (chars_per_second + actual_chars_per_second) / 2
            
            current_time = 0.0
            accumulated_error = 0.0
            
            for i, segment_text in enumerate(segments):
                # Clean segment text
                segment_text = segment_text.strip()
                if not segment_text:
                    continue
                
                # Calculate base duration based on character count
                segment_chars = len(segment_text)
                base_duration = segment_chars / effective_chars_per_second
                
                # Add pause time based on punctuation
                pause_time = calculate_pause_time(segment_text)
                segment_duration = base_duration + pause_time
                
                # Apply smoothing to prevent very short or very long segments
                segment_duration = smooth_duration(segment_duration, segment_chars)
                
                # Adjust for accumulated timing error
                if i < len(segments) - 1:
                    # Not the last segment - adjust timing to stay on track
                    expected_position = (i + 1) / len(segments) * audio_duration
                    predicted_position = current_time + segment_duration
                    timing_error = expected_position - predicted_position
                    
                    # Apply partial correction to avoid abrupt changes
                    correction = timing_error * 0.3
                    segment_duration += correction
                    accumulated_error += timing_error - correction
                else:
                    # Last segment - use remaining time
                    segment_duration = audio_duration - current_time
                
                # Ensure minimum duration for readability
                min_duration = 0.5
                if segment_duration < min_duration and i < len(segments) - 1:
                    segment_duration = min_duration
                
                # Create segment info
                segment_info = {
                    "text": segment_text,
                    "start_time": round(current_time, 2),
                    "end_time": round(min(current_time + segment_duration, audio_duration), 2),
                    "duration": round(segment_duration, 2)
                }
                
                # Validate segment
                if segment_info["end_time"] > segment_info["start_time"]:
                    transcript_data["segments"].append(segment_info)
                    current_time = segment_info["end_time"]
                    
                    logger.info(f"Segment {i+1}: '{segment_text[:40]}...' "
                              f"[{segment_info['start_time']:.2f}-{segment_info['end_time']:.2f}] "
                              f"({segment_duration:.2f}s)")
                
                # Stop if we've reached the end
                if current_time >= audio_duration - 0.1:
                    break
        
        # Final validation and adjustment
        transcript_data = validate_and_adjust_timing(transcript_data, audio_duration)
        
        logger.info(f"ACCURATE transcript generated: {transcript_data['word_count']} words, "
                   f"{len(transcript_data['segments'])} segments")
        
        return transcript_data
        
    except Exception as e:
        logger.error(f"Error generating transcript from script: {str(e)}")
        return create_fallback_transcript(audio_path)

def split_script_into_natural_segments(script):
    """
    Split script into natural segments based on speech patterns
    """
    # First, try to split by sentences
    sentences = split_into_sentences(script)
    segments = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        words = sentence.split()
        word_count = len(words)
        
        # Ideal segment: 5-15 words
        if word_count <= 15:
            segments.append(sentence)
        else:
            # Split long sentences at natural break points
            sub_segments = split_long_sentence(sentence)
            segments.extend(sub_segments)
    
    # If no good segments, fall back to word-based splitting
    if not segments:
        words = script.split()
        for i in range(0, len(words), 10):
            segment = ' '.join(words[i:i+10])
            if segment.strip():
                segments.append(segment.strip())
    
    return segments

def split_into_sentences(text):
    """Split text into sentences with improved handling"""
    # Handle common abbreviations that shouldn't end sentences
    text = re.sub(r'\b(Mr|Mrs|Dr|Ms|Prof|Sr|Jr)\.\s*', r'\1<PERIOD> ', text)
    
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Restore periods in abbreviations
    sentences = [s.replace('<PERIOD>', '.') for s in sentences]
    
    # Handle edge cases
    final_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Check if sentence ends with punctuation
            if not re.search(r'[.!?]$', sentence):
                sentence += '.'
            final_sentences.append(sentence)
    
    return final_sentences

def split_long_sentence(sentence):
    """Split a long sentence at natural break points"""
    segments = []
    
    # Try to split at commas, semicolons, or conjunctions
    parts = re.split(r'[,;]|\s+(?:and|but|or|because|although|while|when)\s+', sentence)
    
    current_segment = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if adding this part would make segment too long
        test_segment = current_segment + " " + part if current_segment else part
        if len(test_segment.split()) > 12 and current_segment:
            segments.append(current_segment.strip())
            current_segment = part
        else:
            current_segment = test_segment
    
    if current_segment.strip():
        segments.append(current_segment.strip())
    
    # If no good splits, use word-based splitting
    if not segments or any(len(s.split()) > 15 for s in segments):
        words = sentence.split()
        segments = []
        for i in range(0, len(words), 10):
            segment = ' '.join(words[i:i+10])
            if segment.strip():
                segments.append(segment.strip())
    
    return segments

def calculate_pause_time(text):
    """Calculate natural pause time based on punctuation"""
    pause_time = 0.0
    
    # Count punctuation marks
    if text.endswith('.'):
        pause_time += 0.3  # Period pause
    elif text.endswith('!') or text.endswith('?'):
        pause_time += 0.4  # Exclamation/question pause
    
    # Count commas
    comma_count = text.count(',')
    pause_time += comma_count * 0.15
    
    # Count other punctuation
    semicolon_count = text.count(';')
    pause_time += semicolon_count * 0.2
    
    colon_count = text.count(':')
    pause_time += colon_count * 0.2
    
    return pause_time

def smooth_duration(duration, char_count):
    """Smooth duration to prevent extreme values"""
    # Minimum: 0.3 seconds per 5 characters
    min_duration = max(0.5, char_count * 0.06)
    
    # Maximum: 0.5 seconds per 5 characters
    max_duration = char_count * 0.1
    
    return max(min_duration, min(duration, max_duration))

def validate_and_adjust_timing(transcript_data, total_duration):
    """Validate and adjust timing to ensure perfect sync"""
    segments = transcript_data.get("segments", [])
    if not segments:
        return transcript_data
    
    # First pass: ensure no overlaps and proper ordering
    for i in range(len(segments)):
        segment = segments[i]
        
        # Ensure start time is not negative
        if segment["start_time"] < 0:
            segment["start_time"] = 0
        
        # Ensure end time doesn't exceed total duration
        if segment["end_time"] > total_duration:
            segment["end_time"] = total_duration
        
        # Ensure proper duration
        if segment["end_time"] <= segment["start_time"]:
            # Remove invalid segment
            segments[i] = None
            continue
        
        segment["duration"] = round(segment["end_time"] - segment["start_time"], 2)
        
        # Ensure no overlap with next segment
        if i < len(segments) - 1:
            next_segment = segments[i + 1]
            if next_segment and segment["end_time"] > next_segment["start_time"]:
                # Create small gap
                segment["end_time"] = next_segment["start_time"] - 0.05
                segment["duration"] = round(segment["end_time"] - segment["start_time"], 2)
    
    # Remove None segments
    segments = [s for s in segments if s is not None]
    
    # Second pass: ensure last segment ends at audio duration
    if segments:
        last_segment = segments[-1]
        if abs(last_segment["end_time"] - total_duration) > 0.1:
            last_segment["end_time"] = total_duration
            last_segment["duration"] = round(last_segment["end_time"] - last_segment["start_time"], 2)
    
    transcript_data["segments"] = segments
    return transcript_data

def create_fallback_transcript(audio_path):
    """Create a fallback transcript structure when speech recognition fails"""
    duration = get_audio_duration(audio_path)
    
    return {
        "full_text": "[Audio content - transcript unavailable]",
        "segments": [{
            "text": "[Audio content - transcript unavailable]",
            "start_time": 0.0,
            "end_time": duration,
            "duration": duration
        }],
        "duration": duration,
        "word_count": 0
    }