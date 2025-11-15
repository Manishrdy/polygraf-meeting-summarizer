import os
import moviepy.editor as mp

def extract_audio():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    #hardcoded values for testing
    input_video = os.path.join(project_root, "data", "bot_AkYnbDBy0YQigs48-rec_vZhODQwGYZHhi3cC.mp4")
    output_audio = os.path.join(project_root, "data", "bot_AkYnbDBy0YQigs48-rec_vZhODQwGYZHhi3cC.wav")

    print(f"Extracting audio from: {input_video}")
    if not os.path.exists(input_video):
        raise FileNotFoundError(f"Input file not found: {input_video}")

    video = mp.VideoFileClip(input_video)
    video.audio.write_audiofile(output_audio, codec="pcm_s16le")
    print(f"Audio extracted successfully: {output_audio}")

if __name__ == "__main__":
    extract_audio()