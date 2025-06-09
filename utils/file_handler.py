import os
import uuid
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'}

def allowed_file(filename, allowed_extensions):
    """
    Check if a file has an allowed extension
    
    Args:
        filename (str): Name of the file
        allowed_extensions (set): Set of allowed extensions
        
    Returns:
        bool: True if file is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder, session_id, file_type):
    """
    Save an uploaded file with proper naming and validation
    
    Args:
        file: Uploaded file object
        upload_folder (str): Directory to save the file
        session_id (str): Unique session identifier
        file_type (str): Type of file (e.g., 'background', 'audio')
        
    Returns:
        str: Path to the saved file
    """
    try:
        if not file or file.filename == '':
            raise ValueError("No file provided")
        
        filename = secure_filename(file.filename)
        
        # Validate file type
        if file_type == 'background':
            if not allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
                raise ValueError(f"Invalid image file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
        elif file_type == 'audio':
            if not allowed_file(filename, ALLOWED_AUDIO_EXTENSIONS):
                raise ValueError(f"Invalid audio file type. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}")
        elif file_type == 'video':
            if not allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS):
                raise ValueError(f"Invalid video file type. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}")
        
        # Generate unique filename
        file_extension = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{session_id}_{file_type}.{file_extension}"
        file_path = os.path.join(upload_folder, new_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the file
        file.save(file_path)
        
        # Verify file was saved
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f"File saved: {file_path} ({os.path.getsize(file_path)} bytes)")
            return file_path
        else:
            raise Exception("File was not saved properly")
            
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise Exception(f"Failed to save file: {str(e)}")

def cleanup_temp_files(session_id, temp_folder):
    """
    Clean up temporary files for a session
    
    Args:
        session_id (str): Session identifier
        temp_folder (str): Temporary files directory
    """
    try:
        if not os.path.exists(temp_folder):
            return
        
        files_removed = 0
        # Look for all files containing the session ID
        import glob
        pattern = os.path.join(temp_folder, f"*{session_id}*")
        temp_files = glob.glob(pattern)
        
        for file_path in temp_files:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    files_removed += 1
                    logger.info(f"Removed temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove {file_path}: {str(e)}")
        
        logger.info(f"Cleaned up {files_removed} temporary files for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")

def cleanup_old_files(folder_path, max_age_hours=24):
    """
    Clean up old files in a directory
    
    Args:
        folder_path (str): Directory to clean
        max_age_hours (int): Maximum age in hours before deletion
    """
    try:
        if not os.path.exists(folder_path):
            return
        
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        files_removed = 0
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        files_removed += 1
                        logger.info(f"Removed old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove {file_path}: {str(e)}")
        
        logger.info(f"Cleaned up {files_removed} old files from {folder_path}")
        
    except Exception as e:
        logger.error(f"Error cleaning up old files: {str(e)}")

def get_file_info(file_path):
    """
    Get information about a file
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        dict: File information
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        
        return {
            "path": file_path,
            "filename": os.path.basename(file_path),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "extension": file_path.rsplit('.', 1)[1].lower() if '.' in file_path else None
        }
        
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return None

def ensure_directories(*directories):
    """
    Ensure that directories exist, create them if they don't
    
    Args:
        *directories: Variable number of directory paths
    """
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory ensured: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")

def get_available_filename(base_path, filename):
    """
    Get an available filename by adding a number suffix if file exists
    
    Args:
        base_path (str): Directory path
        filename (str): Desired filename
        
    Returns:
        str: Available filename
    """
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(base_path, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    
    return new_filename

def calculate_folder_size(folder_path):
    """
    Calculate the total size of all files in a folder
    
    Args:
        folder_path (str): Path to the folder
        
    Returns:
        dict: Size information
    """
    try:
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 3),
            "file_count": file_count
        }
        
    except Exception as e:
        logger.error(f"Error calculating folder size: {str(e)}")
        return {"total_size_bytes": 0, "total_size_mb": 0, "total_size_gb": 0, "file_count": 0}