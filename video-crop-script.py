import os
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("video_cropping.log"),
        logging.StreamHandler()
    ]
)

def get_video_duration(video_path):
    """
    Get the duration of a video in seconds using FFprobe.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        float: Duration of the video in seconds or None if error
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Error getting duration for {video_path}: {result.stderr}")
            return None
        
        duration = float(result.stdout.strip())
        return duration
    
    except Exception as e:
        logging.error(f"Exception while getting duration for {video_path}: {str(e)}")
        return None

def crop_video(input_path, output_path, max_duration=7):
    """
    Crop a video to specified duration if it's longer than that duration.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to save the cropped video
        max_duration: Maximum duration in seconds
        
    Returns:
        bool: True if cropping was successful, False otherwise
    """
    try:
        # First check the video duration
        duration = get_video_duration(input_path)
        
        if duration is None:
            return False
            
        # If video is shorter than or equal to max_duration, just copy it
        if duration <= max_duration:
            logging.info(f"Video {input_path} is already shorter than {max_duration} seconds ({duration:.2f}s). Copying.")
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-c', 'copy',
                str(output_path),
                '-y'  # Overwrite output file if it exists
            ]
        else:
            # Crop the video to max_duration
            logging.info(f"Cropping {input_path} from {duration:.2f}s to {max_duration}s")
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-t', str(max_duration),
                '-c:v', 'copy',  # Copy video codec to avoid re-encoding
                '-c:a', 'copy',  # Copy audio codec to avoid re-encoding
                str(output_path),
                '-y'  # Overwrite output file if it exists
            ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the command was successful
        if result.returncode != 0:
            logging.error(f"Error processing {input_path}: {result.stderr}")
            return False
        
        if duration > max_duration:
            # Get file sizes for logging
            input_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
            output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            size_reduction = (1 - (output_size / input_size)) * 100
            
            logging.info(f"Cropped {input_path}")
            logging.info(f"Original: {input_size:.2f}MB, Cropped: {output_size:.2f}MB, Reduced by: {size_reduction:.2f}%")
        
        return True
    
    except Exception as e:
        logging.error(f"Exception while processing {input_path}: {str(e)}")
        return False

def process_directory(base_dir, output_dir=None, video_extensions=None, max_duration=7):
    """
    Process all video files in the directory structure.
    
    Args:
        base_dir: Base directory containing folders with videos
        output_dir: Directory to save cropped videos (creates similar structure)
        video_extensions: List of video file extensions to process
        max_duration: Maximum duration in seconds
    """
    if video_extensions is None:
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
    
    # If output_dir is not provided, create a "cropped" folder next to base_dir
    if output_dir is None:
        base_path = Path(base_dir)
        output_dir = base_path.parent / f"{base_path.name}_cropped"
    
    base_dir_path = Path(base_dir)
    output_dir_path = Path(output_dir)
    
    # Create the output directory if it doesn't exist
    if not output_dir_path.exists():
        output_dir_path.mkdir(parents=True)
    
    # Walk through the directory structure
    total_videos = 0
    processed_videos = 0
    cropped_videos = 0
    
    for root, dirs, files in os.walk(base_dir):
        # Get the relative path from the base directory
        rel_path = os.path.relpath(root, base_dir)
        
        # Create the corresponding output directory
        if rel_path != '.':
            current_output_dir = output_dir_path / rel_path
            if not current_output_dir.exists():
                current_output_dir.mkdir(parents=True)
        else:
            current_output_dir = output_dir_path
        
        # Process video files
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                total_videos += 1
                input_file = Path(root) / file
                output_file = current_output_dir / file
                
                # Check duration and crop if necessary
                logging.info(f"Processing {input_file}")
                duration = get_video_duration(input_file)
                
                if duration is None:
                    continue
                    
                success = crop_video(input_file, output_file, max_duration)
                
                if success:
                    processed_videos += 1
                    if duration > max_duration:
                        cropped_videos += 1
    
    # Log summary
    logging.info(f"Processing complete.")
    logging.info(f"Processed {processed_videos}/{total_videos} videos.")
    logging.info(f"Cropped {cropped_videos} videos that were longer than {max_duration} seconds.")

if __name__ == "__main__":
    # Configuration
    BASE_DIR = "D:\Capstone\data\compressed_videos"  # Path to the folder containing videos
    OUTPUT_DIR = "D:\Capstone\data\croppedcompressed"  # Where to save cropped videos
    MAX_DURATION = 7  # Maximum duration in seconds
    
    logging.info("Starting video cropping process")
    process_directory(BASE_DIR, OUTPUT_DIR, max_duration=MAX_DURATION)
    logging.info("Process completed")
