import sounddevice as sd
from scipy.io.wavfile import write
import os

SAMPLE_RATE = 16000  
DURATION = 5         

def record_audio(output_path="data/test.wav"):
    print("Enregistrement en cours...")

    os.makedirs("data", exist_ok=True)

    recording = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(output_path, SAMPLE_RATE, recording)

    print(f"Audio sauvegardé dans {output_path}")
