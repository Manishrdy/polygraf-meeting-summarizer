from app.services.consumer import consume_diarized_segments

if __name__ == "__main__":
    segments = consume_diarized_segments(
        json_path="data/response.json",
        audio_path="data/bot_AkYnbDBy0YQigs48-rec_vZhODQwGYZHhi3cC.wav"
    )
    print(f"Total segments created: {len(segments)}")