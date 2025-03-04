import os
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("video_compression.log"),
        logging.StreamHandler()
    ]
)

def compress_video(input_path, output_path, crf=23):
    """
    Compress a video using FFmpeg with H.264 codec.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to save the compressed video
        crf: Constant Rate Factor (18-28 is good, lower means better quality)
    
    Returns:
        bool: True if compression was successful, False otherwise
    """
    try:
        # Create command for FFmpeg
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-crf', str(crf),
            '-preset', 'medium',
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path),
            '-y'  # Overwrite output file if it exists
        ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the command was successful
        if result.returncode != 0:
            logging.error(f"Error compressing {input_path}: {result.stderr}")
            return False
        
        # Get file sizes for logging
        input_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
        output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        compression_ratio = (1 - (output_size / input_size)) * 100
        
        logging.info(f"Compressed {input_path}")
        logging.info(f"Original: {input_size:.2f}MB, Compressed: {output_size:.2f}MB, Saved: {compression_ratio:.2f}%")
        
        return True
    
    except Exception as e:
        logging.error(f"Exception while compressing {input_path}: {str(e)}")
        return False

def process_directory(base_dir, output_dir=None, video_extensions=None, crf=23):
    """
    Process all video files in the directory structure.
    
    Args:
        base_dir: Base directory containing folders with videos
        output_dir: Directory to save compressed videos (creates similar structure)
        video_extensions: List of video file extensions to process
        crf: Compression quality factor
    """
    if video_extensions is None:
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
    
    # If output_dir is not provided, create a "compressed" folder next to base_dir
    if output_dir is None:
        base_path = Path(base_dir)
        output_dir = base_path.parent / f"{base_path.name}_compressed"
    
    base_dir_path = Path(base_dir)
    output_dir_path = Path(output_dir)
    
    # Create the output directory if it doesn't exist
    if not output_dir_path.exists():
        output_dir_path.mkdir(parents=True)
    
    # Walk through the directory structure
    total_videos = 0
    compressed_videos = 0
    total_saved_mb = 0
    
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
                
                # Get original size
                original_size = os.path.getsize(input_file) / (1024 * 1024)  # MB
                
                # Compress the video
                logging.info(f"Processing {input_file}")
                success = compress_video(input_file, output_file, crf)
                
                if success:
                    compressed_videos += 1
                    # Calculate space saved
                    new_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
                    saved_mb = original_size - new_size
                    total_saved_mb += saved_mb
    
    # Log summary
    logging.info(f"Compression complete. Processed {compressed_videos}/{total_videos} videos.")
    logging.info(f"Total space saved: {total_saved_mb:.2f} MB")

if __name__ == "__main__":
    # Configuration
    BASE_DIR = "D:\Capstone\data\downloaded_videos"  # Path to the folder containing videos
    OUTPUT_DIR = "D:\Capstone\data\compressed_videos"  # Where to save compressed videos
    COMPRESSION_QUALITY = 35  # CRF value (18-28 recommended, lower is better quality)
    
    logging.info("Starting video compression process")
    process_directory(BASE_DIR, OUTPUT_DIR, crf=COMPRESSION_QUALITY)
    logging.info("Process completed")
