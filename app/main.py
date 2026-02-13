from audio.recorder import record_audio
from stt.vosk_transcriber import VoskTranscriber
from text_processing.preprocessor import TextPreprocessor

if __name__ == "__main__":
    record_audio()

    transcriber = VoskTranscriber()
    raw_text = transcriber.transcribe("data/test.wav")

    print("📝 Texte brut :", raw_text)

    preprocessor = TextPreprocessor()
    clean_text = preprocessor.clean(raw_text)

    print("🧹 Texte nettoyé :", clean_text)
