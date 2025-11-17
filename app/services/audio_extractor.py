import os
import moviepy.editor as mp
from app.logger import get_logger

logger = get_logger(__name__)

logger.info("Inside audio_extractor in app.services")

def extract_audio(input_path, output_path):

    logger.info(f"Video .mp4 path: {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"file not found: {input_path}")
    
    try:
        video = mp.VideoFileClip(input_path)
        video.audio.write_audiofile(output_path, codec="pcm_s16le", verbose=False, logger=None)
        
        video.close()
        logger.info(f"Audio extracted successfully: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Failed extracting audio: {e}")
        raise