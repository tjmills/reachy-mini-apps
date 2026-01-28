import numpy as np
import time
from reachy_mini import ReachyMini

def main():
    # gstreamer backend required on robot (Wireless)
    with ReachyMini(media_backend="gstreamer") as mini:
        sr = mini.media.get_input_audio_samplerate()  # 16000 Hz
        record_duration = 3.0

        # Record audio from microphone (accumulate chunks)
        print(f"Recording for {record_duration} seconds...")
        mini.media.start_recording()
        chunks = []
        start = time.time()
        while time.time() - start < record_duration:
            chunk = mini.media.get_audio_sample()
            if chunk is not None:
                chunks.append(chunk)
        mini.media.stop_recording()

        if not chunks:
            print("No audio recorded!")
            return

        samples = np.concatenate(chunks, axis=0)
        print(f"Recorded {len(samples)} samples ({len(samples)/sr:.1f}s) at {sr}Hz")

        # Play back the recording
        print("Playing back...")
        mini.media.start_playing()
        mini.media.push_audio_sample(samples)
        time.sleep(len(samples) / sr + 0.1)
        mini.media.stop_playing()

        print("Done!")

if __name__ == "__main__":
    main()
