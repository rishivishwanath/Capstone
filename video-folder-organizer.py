import pandas as pd
import os
import requests
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

def extract_file_id(drive_link):
    """Extract the file ID from various formats of Google Drive links"""
    patterns = [
        r'\/d\/([a-zA-Z0-9-_]+)',  # /d/ format
        r'id=([a-zA-Z0-9-_]+)',    # id= format
        r'\/file\/d\/([a-zA-Z0-9-_]+)'  # /file/d/ format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, drive_link)
        if match:
            return match.group(1)
    return None

def setup_drive_service():
    """Set up and authenticate Google Drive API"""
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    return build('drive', 'v3', credentials=creds)

def sanitize_folder_name(name):
    """Remove invalid characters from folder names"""
    # Replace invalid characters with underscore
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', str(name))

def download_video(service, file_id, output_path):
    """Download a video file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        
        print(f"Downloading to {output_path}")
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download Progress: {int(status.progress() * 100)}%")
            
        file.seek(0)
        with open(output_path, 'wb') as f:
            f.write(file.read())
        return True
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return False

def process_videos():
    # Read the Excel file
    try:
        df = pd.read_excel('dataset.xlsx')  # Replace with your Excel file name
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return

    # Verify required columns exist
    if 'video_name' not in df.columns or 'Download' not in df.columns:
        print("Error: Required columns 'video_name' and 'Download' not found in Excel file")
        return

    # Set up Google Drive service
    try:
        service = setup_drive_service()
    except Exception as e:
        print(f"Error setting up Google Drive service: {str(e)}")
        return

    # Create base directory for all videos
    base_dir = 'downloaded_videos'
    os.makedirs(base_dir, exist_ok=True)

    # Process each row
    for index, row in df.iterrows():
        video_name = sanitize_folder_name(row['video_name'])
        drive_link = row['Download']

        # Skip if any required field is empty
        if pd.isna(video_name) or pd.isna(drive_link):
            print(f"Skipping row {index + 2}: Missing required information")
            continue

        # Create folder for video
        folder_path = os.path.join(base_dir, video_name)
        os.makedirs(folder_path, exist_ok=True)

        # Extract file ID from drive link
        file_id = extract_file_id(drive_link)
        if not file_id:
            print(f"Could not extract file ID from link for {video_name}")
            continue

        try:
            # Get file metadata to determine original filename
            file_metadata = service.files().get(fileId=file_id, fields='name').execute()
            original_filename = file_metadata['name']
            
            # Create full output path
            output_path = os.path.join(folder_path, original_filename)
            
            # Download the video
            print(f"\nProcessing video: {video_name}")
            if download_video(service, file_id, output_path):
                print(f"Successfully downloaded {original_filename} to {folder_path}")
            else:
                print(f"Failed to download video for {video_name}")
                
        except Exception as e:
            print(f"Error processing {video_name}: {str(e)}")

if __name__ == '__main__':
    print("Starting video download and organization process...")
    process_videos()
    print("\nProcess completed!")
