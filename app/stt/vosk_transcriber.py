from vosk import Model, KaldiRecognizer
import wave
import json
import os

MODEL_PATH = "models/vosk/vosk-model-small-fr-0.22"

class VoskTranscriber:

    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise Exception("Modèle Vosk introuvable")
        
        print("🔄 Chargement du modèle Vosk...")
        self.model = Model(MODEL_PATH)
        print("✅ Modèle chargé")

    def transcribe(self, audio_path):
        wf = wave.open(audio_path, "rb")

        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)

        text_result = ""

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text_result += result.get("text", "") + " "

        final_result = json.loads(rec.FinalResult())
        text_result += final_result.get("text", "")

        wf.close()

        return text_result.strip()
