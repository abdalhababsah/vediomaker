from moviepy import VideoFileClip, ImageClip, TextClip, ColorClip, CompositeVideoClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import logging
import textwrap

logger = logging.getLogger(__name__)

def create_video_with_transcript(background_path, audio_path, transcript_data, output_folder, session_id):
    """Create video combining background image, audio, and subtitles"""
    try:
        logger.info(f"Creating video for session {session_id}")
        
        # Validate inputs
        if not os.path.exists(background_path):
            raise Exception(f"Background image not found: {background_path}")
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
        if not transcript_data or not transcript_data.get('segments'):
            raise Exception("Invalid transcript data provided")
        
        # Load audio clip
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        logger.info(f"Audio duration: {duration} seconds")
        
        if duration <= 0:
            raise Exception("Invalid audio duration")
        
        # Create background video clip using ORIGINAL image dimensions
        background_clip = create_background_clip(background_path, duration)
        logger.info(f"Background clip created: {background_clip.size}")
        
        # Create subtitle clips
        subtitle_clips = create_subtitle_clips_improved(transcript_data, background_clip.size, duration)
        logger.info(f"Created {len(subtitle_clips)} subtitle clips")
        
        # Combine all elements
        if subtitle_clips:
            final_video = CompositeVideoClip([background_clip] + subtitle_clips)
            logger.info("✅ Subtitles added to video")
        else:
            final_video = background_clip
            logger.warning("⚠️  No subtitles added - using background only")
        
        # Add audio
        final_video = final_video.with_audio(audio_clip)
        
        # Generate output path
        output_filename = f"{session_id}_final_video.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        # Ensure output directory exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Write the video file
        logger.info("Writing video file...")
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset='medium',
            ffmpeg_params=['-crf', '23']
        )
        
        # Clean up clips
        audio_clip.close()
        background_clip.close()
        for clip in subtitle_clips:
            if hasattr(clip, 'close'):
                clip.close()
        final_video.close()
        
        # Verify output file was created
        if not os.path.exists(output_path):
            raise Exception("Video file was not created successfully")
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise Exception("Created video file is empty")
        
        logger.info(f"Video created successfully: {output_path} ({file_size} bytes)")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise Exception(f"Failed to create video: {str(e)}")

def create_background_clip(background_path, duration):
    """Create background video clip using ORIGINAL image dimensions"""
    try:
        # Get original image dimensions first
        with Image.open(background_path) as img:
            original_width, original_height = img.size
            logger.info(f"Original image size: {original_width}x{original_height}")
        
        # Create ImageClip with original dimensions
        img_clip = ImageClip(background_path)
        
        # Keep original dimensions - no resizing!
        target_width, target_height = original_width, original_height
        
        # Only resize if image is extremely large (over 4K) for performance
        if original_width > 3840 or original_height > 2160:
            # Scale down while maintaining aspect ratio
            scale = min(3840 / original_width, 2160 / original_height)
            target_width = int(original_width * scale)
            target_height = int(original_height * scale)
            
            img_clip = img_clip.resized((target_width, target_height))
            logger.info(f"Scaled down large image to: {target_width}x{target_height}")
        else:
            # Use original dimensions
            logger.info(f"Using original image dimensions: {target_width}x{target_height}")
        
        # Set duration
        img_clip = img_clip.with_duration(duration)
        
        logger.info(f"Background clip created: {img_clip.size}, {duration}s")
        return img_clip
        
    except Exception as e:
        logger.error(f"Error creating background clip: {str(e)}")
        # Fallback: try to get image dimensions for fallback
        try:
            with Image.open(background_path) as img:
                width, height = img.size
            fallback_clip = ColorClip(size=(width, height), color=(20, 20, 40), duration=duration)
        except:
            # Ultimate fallback
            fallback_clip = ColorClip(size=(1920, 1080), color=(20, 20, 40), duration=duration)
        
        logger.info("Created fallback colored background")
        return fallback_clip

def create_subtitle_clips_improved(transcript_data, video_size, total_duration):
    """Create subtitle clips with improved handling"""
    try:
        subtitle_clips = []
        segments = transcript_data.get('segments', [])
        
        if not segments:
            return []
        
        for i, segment in enumerate(segments):
            try:
                text = segment.get('text', '').strip()
                start_time = float(segment.get('start_time', 0))
                end_time = float(segment.get('end_time', 0))
                
                # Validate segment data
                if not text or start_time >= end_time:
                    continue
                
                if end_time > total_duration + 0.1:
                    end_time = total_duration
                
                if start_time >= total_duration:
                    continue
                
                duration = end_time - start_time
                if duration < 0.1:
                    continue
                
                # Create subtitle clip
                subtitle_clip = create_subtitle_clip_robust(text, start_time, duration, video_size)
                
                if subtitle_clip:
                    subtitle_clips.append(subtitle_clip)
                    
            except Exception as e:
                logger.error(f"Error processing segment {i+1}: {str(e)}")
                continue
        
        return subtitle_clips
        
    except Exception as e:
        logger.error(f"Error creating subtitle clips: {str(e)}")
        return []

def create_subtitle_clip_robust(text, start_time, duration, video_size):
    """Create subtitle with multiple fallback methods"""
    methods = [
        create_subtitle_image_clip,
        create_textclip_caption,
        create_textclip_simple,
        create_fallback_subtitle
    ]
    
    for method in methods:
        try:
            if method == create_subtitle_image_clip:
                clip = method(text, start_time, duration, video_size)
            else:
                clip = method(text, start_time, duration, video_size)
            
            if clip:
                return clip
                
        except Exception as e:
            continue
    
    return None

def create_subtitle_image_clip(text, start_time, duration, video_size, font_size=None):
    """Create subtitle using PIL image generation with adaptive font size"""
    try:
        text = clean_text_for_display(text)
        wrapped_text = wrap_text_for_subtitles(text, max_chars_per_line=60)
        lines = wrapped_text.split('\n')
        
        width, height = video_size
        
        # Adaptive font size based on video dimensions
        if font_size is None:
            font_size = max(24, min(48, width // 40))  # Scale font to video size
        
        line_height = font_size + 10
        subtitle_height = len(lines) * line_height + 40
        
        img = Image.new('RGBA', (width, subtitle_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        font = get_best_available_font(font_size)
        
        y_offset = 20
        for line in lines:
            if not line.strip():
                y_offset += line_height
                continue
            
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_offset
            
            # Draw outline
            outline_width = max(2, font_size // 16)
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
            
            # Draw main text
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y_offset += line_height
        
        img_array = np.array(img)
        subtitle_img_clip = ImageClip(img_array, duration=duration, transparent=True)
        subtitle_img_clip = subtitle_img_clip.with_position(('center', height - subtitle_height - 50))
        subtitle_img_clip = subtitle_img_clip.with_start(start_time)
        
        return subtitle_img_clip
        
    except Exception as e:
        raise

def create_textclip_caption(text, start_time, duration, video_size):
    """Create subtitle using TextClip caption method"""
    try:
        text = clean_text_for_display(text)
        wrapped_text = wrap_text_for_subtitles(text, max_chars_per_line=50)
        
        # Adaptive font size
        font_size = max(24, min(42, video_size[0] // 45))
        
        txt_clip = TextClip(
            wrapped_text,
            fontsize=font_size,
            color='white',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(video_size[0] - 200, None),
            align='center'
        )
        
        txt_clip = txt_clip.with_position(('center', video_size[1] - 200))
        txt_clip = txt_clip.with_start(start_time)
        txt_clip = txt_clip.with_duration(duration)
        
        return txt_clip
        
    except Exception as e:
        raise

def create_textclip_simple(text, start_time, duration, video_size):
    """Create subtitle using simple TextClip"""
    try:
        text = clean_text_for_display(text)
        wrapped_text = wrap_text_for_subtitles(text, max_chars_per_line=40)
        
        # Adaptive font size
        font_size = max(20, min(38, video_size[0] // 50))
        
        txt_clip = TextClip(
            wrapped_text,
            fontsize=font_size,
            color='white',
            stroke_color='black',
            stroke_width=1
        )
        
        txt_clip = txt_clip.with_position(('center', video_size[1] - 150))
        txt_clip = txt_clip.with_start(start_time)
        txt_clip = txt_clip.with_duration(duration)
        
        return txt_clip
        
    except Exception as e:
        raise

def create_fallback_subtitle(text, start_time, duration, video_size):
    """Create fallback subtitle with colored background"""
    try:
        text = clean_text_for_display(text)
        wrapped_text = wrap_text_for_subtitles(text, max_chars_per_line=35)
        
        bg_width = min(len(wrapped_text) * 15, video_size[0] - 100)
        bg_height = wrapped_text.count('\n') * 30 + 60
        
        bg_clip = ColorClip(
            size=(bg_width, bg_height),
            color=(0, 0, 0),
            duration=duration
        ).with_opacity(0.7)
        
        # Adaptive font size
        font_size = max(18, min(32, video_size[0] // 60))
        
        txt_clip = TextClip(
            wrapped_text,
            fontsize=font_size,
            color='white'
        ).with_duration(duration)
        
        subtitle_clip = CompositeVideoClip([
            bg_clip.with_position('center'),
            txt_clip.with_position('center')
        ]).with_duration(duration)
        
        subtitle_clip = subtitle_clip.with_position(('center', video_size[1] - 120))
        subtitle_clip = subtitle_clip.with_start(start_time)
        
        return subtitle_clip
        
    except Exception as e:
        raise

def get_best_available_font(font_size):
    """Try to load the best available font"""
    font_paths = [
        "arial.ttf",
        "/System/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, font_size)
        except:
            continue
    
    try:
        return ImageFont.load_default()
    except:
        return None

def clean_text_for_display(text):
    """Clean text for better subtitle display"""
    if not text:
        return ""
    
    text = ' '.join(text.split())
    text = text.replace('\u2014', '--')
    text = text.replace('\u2013', '-')
    text = text.replace('\u2018', "'")
    text = text.replace('\u2019', "'")
    text = text.replace('\u201c', '"')
    text = text.replace('\u201d', '"')
    text = text.replace('\u2026', '...')
    
    return text.strip()

def wrap_text_for_subtitles(text, max_chars_per_line=60):
    """Wrap text for optimal subtitle display"""
    if not text:
        return ""
    
    if len(text) <= max_chars_per_line:
        return text
    
    wrapped_lines = textwrap.wrap(
        text, 
        width=max_chars_per_line,
        break_long_words=False,
        break_on_hyphens=True
    )
    
    if len(wrapped_lines) > 2:
        words = text.split()
        mid_point = len(words) // 2
        
        line1 = ' '.join(words[:mid_point])
        line2 = ' '.join(words[mid_point:])
        
        if len(line1) > max_chars_per_line:
            line1 = line1[:max_chars_per_line-3] + "..."
        if len(line2) > max_chars_per_line:
            line2 = line2[:max_chars_per_line-3] + "..."
            
        return f"{line1}\n{line2}"
    
    return '\n'.join(wrapped_lines)