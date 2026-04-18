from audio.recorder import record_audio
from stt.vosk_transcriber import VoskTranscriber
from text_processing.preprocessor import TextPreprocessor
from text_mining.engine import TextMiningEngine
from database.repository import SQLiteRepository

def process_pipeline():
    try:
        print("\n🎤 Enregistrement...")
        record_audio("data/test.wav")

        # STT
        transcriber = VoskTranscriber()
        raw_text = transcriber.transcribe("data/test.wav")
        print("Texte brut :", raw_text)

        # Nettoyage
        preprocessor = TextPreprocessor()
        clean_text = preprocessor.clean(raw_text)
        print("Texte nettoyé :", clean_text)

        if not clean_text.strip():
            print("⚠️ Texte vide")
            return

        # TEXT MINING
        tm_engine = TextMiningEngine()
        tm_result = tm_engine.score(clean_text)

        score = tm_result["score_tm"]

        # Décision simple (SANS LLM)
        if score < 50:
            label = "NORMAL"
        elif score < 72:
            label = "URGENT"
        else:
            label = "CRITIQUE"

        print("\n🧠 RESULTAT :")
        print("Score :", score)
        print("Label :", label)

        # Simulation LED
        if label in ["URGENT", "CRITIQUE"]:
            print("🔴 LED ON (simulation)")
        else:
            print("🟢 LED OFF (simulation)")

        # Sauvegarde DB
        db = SQLiteRepository()
        db.insert_log(
            transcript=clean_text,
            score_tm=score,
            score_llm=0,
            score_final=score,
            label_final=label,
            justification="Mode PC sans LLM"
        )

        print("💾 Log enregistré")

    except Exception as e:
        print("❌ Erreur :", e)


if __name__ == "__main__":
    print("👉 Mode PC prêt")
    print("Appuie sur ENTER pour simuler le bouton")

    while True:
        input("\n👉 ENTER...")
        process_pipeline()