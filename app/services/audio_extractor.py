import os
import moviepy.editor as mp
from app.logger import get_logger

logger = get_logger(__name__)

logger.info("Inside audio_extractor in app.services")

def extract_audio(input_video_path, output_audio_path):

    logger.info(f"Extracting audio from: {input_video_path}")
    
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input file not found: {input_video_path}")
    
    try:
        video = mp.VideoFileClip(input_video_path)
        video.audio.write_audiofile(output_audio_path, codec="pcm_s16le", verbose=False, logger=None)
        video.close()
        logger.info(f"Audio extracted successfully: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        raise