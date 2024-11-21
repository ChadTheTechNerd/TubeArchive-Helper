#############################################################################################################
#           Tubearchive_new.py - A script to archive videos from TubeArchivist downloads to a different     #
#           local directory, updating the metadata, pulling a .nfo file, pulling the thumbnail, and marking #
#           The video as watched on the TubeArchivist Server.                                               #
#                                                                                                           #
#        This script requires the environment variables to be within the .env file:                         #
#        TA_MEDIA_FOLDER - The directory where TubeArchivist downloads the videos                           #
#        TARGET_FOLDER - The directory where the videos will be copied to                                   #
#        TA_API_VIDEO_URL - The URL to the TubeArchivist API for video metadata                             #
#        TA_API_URL - The URL to the TubeArchivist API for login and watched status                         #
#        TA_API_USERNAME - The username for the TubeArchivist API                                           #
#        TA_API_PASSWORD - The password for the TubeArchivist API                                           #
#############################################################################################################
import os
import sys
import shutil
import requests
import logging
import subprocess
import json  # Import the json module
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    filename='tubearchivist_2.log',
    level=logging.DEBUG,
    format='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TA_MEDIA_FOLDER = os.getenv('TA_MEDIA_FOLDER')
TARGET_FOLDER = os.getenv('TARGET_FOLDER')
TA_API_VIDEO_URL = os.getenv('TA_API_VIDEO_URL')
TA_API_URL = os.getenv('TA_API_URL')
TA_API_USERNAME = os.getenv('TA_API_USERNAME')
TA_API_PASSWORD = os.getenv('TA_API_PASSWORD')
THUMB_BASE_URL = os.getenv('THUMB_BASE_URL')  # Base URL for thumbnail paths

def login():
    login_url = f'{TA_API_URL}/login/'
    data = {
        "username": TA_API_USERNAME,
        "password": TA_API_PASSWORD
    }
    logger.debug(f"Logging in at {login_url} with username {TA_API_USERNAME}")
    try:
        response = requests.post(login_url, json=data, timeout=10)
        response.raise_for_status()
        token = response.json().get('token')
        logger.debug(f"Received token: {token}")
        return token
    except requests.exceptions.RequestException as e:
        logger.error(f"Login failed: {e}")
        if e.response is not None:
            logger.error(f"Response content: {e.response.content.decode()}")
        return None

def fetch_metadata(video_id, token):
    logger.debug(f"Fetching metadata for video ID: {video_id}")
    headers = {'Authorization': f'Token {token}'}
    url = f'{TA_API_VIDEO_URL}/{video_id}'
    logger.debug(f"API URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        logger.debug(f"API response status: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Unexpected response: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

def download_thumbnail(vid_thumb_url, thumb_path, token):
    logger.debug(f"Downloading thumbnail from {vid_thumb_url} to {thumb_path}")
    if not vid_thumb_url.startswith('http://') and not vid_thumb_url.startswith('https://'):
        vid_thumb_url = f"{THUMB_BASE_URL.rstrip('/')}/{vid_thumb_url.lstrip('/')}"
    headers = {'Authorization': f'Token {token}'}
    logger.debug(f"Complete thumbnail URL: {vid_thumb_url}")
    logger.debug(f"Request headers: {headers}")

    # Set up retry logic
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.get(vid_thumb_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        with open(thumb_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Thumbnail downloaded at {thumb_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download thumbnail: {e}")

def copy_video_and_embed_metadata(src, dst, metadata, token):
    logger.debug(f"Copying video from {src} to {dst} with metadata {metadata}")
    try:
        if not os.path.exists(src):
            logger.error(f"Source file does not exist: {src}")
            return

        # Create the destination directory if it does not exist
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        logger.debug(f"Destination directory created: {os.path.dirname(dst)}")

        # Copy the video file
        shutil.copy2(src, dst)
        logger.info(f"Copied video from {src} to {dst}")

        # Output all metadata to a .nfo file in the output directory
        nfo_path = os.path.splitext(dst)[0] + '.nfo'
        with open(nfo_path, 'w') as nfo_file:
            json.dump(metadata, nfo_file, indent=4)
        logger.info(f"Exported metadata to {nfo_path}")

        # Prepare metadata for embedding
        metadata_args = []
        if 'data' in metadata:
            data = metadata['data']
            if 'title' in data:
                metadata_args.extend(['-metadata', f'title={data["title"]}'])
            if 'description' in data:
                metadata_args.extend(['-metadata', f'comment={data["description"]}'])
            if 'published' in data:
                metadata_args.extend(['-metadata', f'date={data["published"]}'])
            if 'channel' in data:
                metadata_args.extend(['-metadata', f'artist={data["channel"]["channel_name"]}'])
            # Add any additional metadata fields here

        # Set the metadata for season to 1
        metadata_args.extend(['-metadata', 'season_number=1'])

        # Embed metadata using FFmpeg
        temp_dst = dst + '.tmp'
        ffmpeg_cmd = ['ffmpeg', '-loglevel', 'quiet', '-i', dst, *metadata_args, '-c', 'copy', '-f', 'mp4', temp_dst]
        subprocess.run(ffmpeg_cmd, check=True)
        shutil.move(temp_dst, dst)
        logger.info(f"Embedded metadata into {dst}")

        # Download thumbnail if available
        vid_thumb_url = metadata['data'].get('vid_thumb_url')
        if vid_thumb_url:
            thumb_path = os.path.splitext(dst)[0] + '.jpg'
            download_thumbnail(vid_thumb_url, thumb_path, token)
    except OSError as e:
        logger.error(f"Failed to copy video or export metadata: {e}")

def update_watched_status(video_id, token, position=100):
    progress_url = f'{TA_API_VIDEO_URL}/{video_id}/progress/'
    watched_url = f'{TA_API_URL}/watched/'
    headers = {'Authorization': f'Token {token}'}

    # Update player position
    data_progress = {'position': position}
    try:
        response = requests.post(progress_url, headers=headers, json=data_progress, timeout=10)
        response.raise_for_status()
        logger.info(f"Updated watched position for video ID: {video_id} to position: {position}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update watched position for video ID: {video_id}: {e}")

    # Mark as watched
    data_watched = {'id': video_id, 'is_watched': True}
    try:
        response = requests.post(watched_url, headers=headers, json=data_watched, timeout=10)
        response.raise_for_status()
        logger.info(f"Marked video ID: {video_id} as watched")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to mark video ID: {video_id} as watched: {e}")

def check_watched_status(video_id, token):
    # Construct the URL to check the watched status of the video
    url = f'{TA_API_VIDEO_URL}/{video_id}/progress/'
    headers = {'Authorization': f'Token {token}'}
    try:
        # Send a GET request to the API to check the watched status
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Watched status response for video ID {video_id}: {data}")
        # Return the watched status from the response data
        return data.get('watched', False)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch watched status for video ID: {video_id}: {e}")
        return False

def process_files_in_directory(directory, token):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            logger.debug(f"Processing file: {filename}")
            if filename.endswith('.mp4'):  # Adjust the extension as needed
                src = os.path.join(root, filename)
                video_id = os.path.splitext(filename)[0]

                logger.debug(f"Source path: {src}, Video ID: {video_id}")

                # Check if the file is already watched
                if check_watched_status(video_id, token):
                    logger.info(f"File {src} is already watched, skipping...")
                    continue

                # Fetch metadata
                try:
                    metadata = fetch_metadata(video_id, token)
                    if metadata:
                        title = metadata['data'].get('title', video_id).replace(' ', '_').replace('/', '_')
                        channel_name = metadata['data']['channel'].get('channel_name', 'Unknown_Channel').replace(' ', '_').replace('/', '_')
                        dst = os.path.join(TARGET_FOLDER, channel_name, title + '.mp4')

                        # Skip files that have already been copied
                        if os.path.exists(dst):
                            logger.info(f"File {dst} already exists, skipping...")
                            continue

                        logger.debug(f"Destination path: {dst}, Title: {title}, Channel Name: {channel_name}")

                        # Copy video and embed metadata
                        copy_video_and_embed_metadata(src, dst, metadata, token)

                        # Mark the file as watched
                        update_watched_status(video_id, token)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to fetch metadata for {filename}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error while processing file {filename}: {e}")

if __name__ == "__main__":
    logger.debug("Script started")
    if not all([TA_MEDIA_FOLDER, TARGET_FOLDER, TA_API_VIDEO_URL, TA_API_USERNAME, TA_API_PASSWORD, THUMB_BASE_URL]):
        logger.error("Environment variables TA_MEDIA_FOLDER, TARGET_FOLDER, TA_API_VIDEO_URL, TA_API_USERNAME, TA_API_PASSWORD, and THUMB_BASE_URL must be set.")
        sys.exit(1)

    logger.debug(f"TA_MEDIA_FOLDER: {TA_MEDIA_FOLDER}")
    logger.debug(f"TARGET_FOLDER: {TARGET_FOLDER}")

    token = login()
    if token:
        process_files_in_directory(TA_MEDIA_FOLDER, token)
    else:
        logger.error("Failed to retrieve token, exiting.")

    logger.debug("Script finished")
