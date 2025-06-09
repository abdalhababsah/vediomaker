from flask import Flask, request, jsonify, send_file
import os
import uuid
from datetime import datetime
from services.voice_generator import generate_voiceover
from services.transcript_generator import generate_transcript, generate_transcript_from_script_and_audio
from services.video_creator import create_video_with_transcript
from utils.file_handler import save_uploaded_file, cleanup_temp_files
import logging
from config import DEFAULT_VOICE_PROVIDER, DEFAULT_VOICE_STYLE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
TEMP_FOLDER = 'temp'

# Create necessary directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/create-video', methods=['POST'])
def create_video():
    """
    Main endpoint to create video from script and background image
    
    Expected form data:
    - script: Text script for voiceover
    - background_image: Background image file
    - voice_style: Voice style - 'normal', 'wise', 'elder', 'narrator', 'storyteller' (optional, default: 'elder')
    - voice_provider: Voice provider - 'free' or '11' (optional, default: 'free')
    """
    try:
        # Validate request
        if 'script' not in request.form:
            return jsonify({"error": "Script is required"}), 400
        
        if 'background_image' not in request.files:
            return jsonify({"error": "Background image is required"}), 400
        
        script = request.form['script']
        background_image = request.files['background_image']
        voice_style = request.form.get('voice_style', DEFAULT_VOICE_STYLE)  # Use default from config
        voice_provider = request.form.get('voice_provider', DEFAULT_VOICE_PROVIDER)  # Use default from config
        
        if not script.strip():
            return jsonify({"error": "Script cannot be empty"}), 400
        
        if background_image.filename == '':
            return jsonify({"error": "No background image selected"}), 400
        
        # Validate voice style
        valid_voice_styles = ['normal', 'wise', 'elder', 'narrator', 'storyteller']
        if voice_style not in valid_voice_styles:
            return jsonify({"error": f"Invalid voice style. Choose from: {', '.join(valid_voice_styles)}"}), 400
            
        # Validate voice provider
        valid_providers = ['free', '11']
        if voice_provider not in valid_providers:
            return jsonify({"error": f"Invalid voice provider. Choose from: {', '.join(valid_providers)}"}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Starting video creation for session: {session_id}")
        
        # Step 1: Save background image
        background_path = save_uploaded_file(background_image, UPLOAD_FOLDER, session_id, 'background')
        logger.info(f"Background image saved: {background_path}")
        
        # Step 2: Generate voiceover from script
        logger.info(f"Generating voiceover with {voice_style} voice using {voice_provider} provider...")
        voice_path = generate_voiceover(script, TEMP_FOLDER, session_id, voice_style=voice_style, voice_provider=voice_provider)
        logger.info(f"Voiceover generated: {voice_path}")
        
        # Step 3: Generate transcript from voice (using original script for better accuracy)
        logger.info("Generating transcript...")
        transcript_data = generate_transcript_from_script_and_audio(script, voice_path)
        logger.info("Transcript generated successfully")
        
        # Step 4: Create video with voice, transcript, and background
        logger.info("Creating final video...")
        video_path = create_video_with_transcript(
            background_path, 
            voice_path, 
            transcript_data, 
            OUTPUT_FOLDER, 
            session_id
        )
        logger.info(f"Video created: {video_path}")
        
        # Clean up temporary files
        cleanup_temp_files(session_id, TEMP_FOLDER)
        
        return jsonify({
            "success": True,
            "message": "Video created successfully",
            "session_id": session_id,
            "video_path": video_path,
            "download_url": f"/download/{session_id}",
            "voice_provider": voice_provider
        })
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        return jsonify({"error": f"Failed to create video: {str(e)}"}), 500

@app.route('/download/<session_id>', methods=['GET'])
def download_video(session_id):
    """Download the generated video"""
    try:
        video_path = os.path.join(OUTPUT_FOLDER, f"{session_id}_final_video.mp4")
        
        if not os.path.exists(video_path):
            return jsonify({"error": "Video not found"}), 404
        
        return send_file(
            video_path,
            as_attachment=True,
            download_name=f"generated_video_{session_id}.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return jsonify({"error": "Failed to download video"}), 500

@app.route('/list-videos', methods=['GET'])
def list_videos():
    """List all generated videos"""
    try:
        videos = []
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith('.mp4'):
                session_id = filename.replace('_final_video.mp4', '')
                file_path = os.path.join(OUTPUT_FOLDER, filename)
                file_stats = os.stat(file_path)
                
                videos.append({
                    "session_id": session_id,
                    "filename": filename,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "download_url": f"/download/{session_id}"
                })
        
        videos.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify({"videos": videos})
        
    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        return jsonify({"error": "Failed to list videos"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)