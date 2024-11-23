import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    filename='nfo_process.log',
    level=logging.DEBUG,
    format='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_nfo_file(video_id, metadata, target_folder):
    # Determine the output path for the .nfo file
    nfo_filename = f"{video_id}.nfo"
    nfo_path = os.path.join(target_folder, nfo_filename)
    
    try:
        # Extract necessary fields from metadata
        data = metadata.get('data', {})
        title = data.get('title', '')
        plot = data.get('description', '')
        season = '1'
        vid_thumb_url = f"./{video_id}.jpg"
        duration = data.get('player', {}).get('duration', 0)
        streams = data.get('streams', [])
        
        # Create XML structure
        nfo_content = f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<episodedetails>
  <plot>{plot}</plot>
  <lockdata>false</lockdata>
  <dateadded>{data.get('vid_last_refresh', '')}</dateadded>
  <title>{title}</title>
  <runtime>{duration}</runtime>
  <art>
    <poster>{vid_thumb_url}</poster>
  </art>
  <showtitle />
  <season>{season}</season>
  <fileinfo>
    <streamdetails>"""
        
        for stream in streams:
            if stream['type'] == 'video':
                nfo_content += f"""
      <video>
        <codec>{stream.get('codec', '')}</codec>
        <micodec>{stream.get('codec', '')}</micodec>
        <bitrate>{stream.get('bitrate', 0)}</bitrate>
        <width>{stream.get('width', 0)}</width>
        <height>{stream.get('height', 0)}</height>
        <framerate>24.000076</framerate>
        <language>und</language>
        <scantype>progressive</scantype>
        <default>True</default>
        <forced>False</forced>
        <duration>0</duration>
        <durationinseconds>{duration}</durationinseconds>
      </video>"""
            elif stream['type'] == 'audio':
                nfo_content += f"""
      <audio>
        <codec>{stream.get('codec', '')}</codec>
        <micodec>{stream.get('codec', '')}</micodec>
        <bitrate>{stream.get('bitrate', 0)}</bitrate>
        <language>eng</language>
        <scantype>progressive</scantype>
        <channels>2</channels>
        <samplingrate>48000</samplingrate>
        <default>True</default>
        <forced>False</forced>
      </audio>"""
        
        nfo_content += """
    </streamdetails>
  </fileinfo>
</episodedetails>"""
        
        # Write to .nfo file
        with open(nfo_path, 'w') as nfo_file:
            nfo_file.write(nfo_content)
        logger.info(f"Exported metadata to {nfo_path}")
    except Exception as e:
        logger.error(f"Failed to export metadata to {nfo_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        logger.error("Usage: nfo_process.py <video_id> <metadata_json> <target_folder>")
        sys.exit(1)

    video_id = sys.argv[1]
    metadata_json = sys.argv[2]
    target_folder = sys.argv[3]

    try:
        metadata = json.loads(metadata_json)
        create_nfo_file(video_id, metadata, target_folder)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode metadata JSON: {e}")
        sys.exit(1)
