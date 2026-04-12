from audio.recorder import record_audio
from stt.vosk_transcriber import VoskTranscriber
from text_processing.preprocessor import TextPreprocessor
from text_mining.engine import TextMiningEngine
from decision.engine import DecisionEngine
from llm.classifier import LLMClassifier
from database.repository import SQLiteRepository
from arduino.serial_client import ArduinoClient


if __name__ == "__main__":
    record_audio()

    transcriber = VoskTranscriber()
    raw_text = transcriber.transcribe("data/test.wav")
    print("Texte brut :", raw_text)

    preprocessor = TextPreprocessor()
    clean_text = preprocessor.clean(raw_text)
    print("Texte nettoyé :", clean_text)

    if not clean_text.strip():
        print("Texte vide → NORMAL")
        exit()

    tm_engine = TextMiningEngine()
    tm_result = tm_engine.score(clean_text)
    print("Résultat Text Mining :", tm_result)

    llm_classifier = LLMClassifier()
    llm_result = llm_classifier.classify(clean_text)
    print("Résultat LLM :", llm_result)

    decision_engine = DecisionEngine()
    final_decision = decision_engine.fuse_tm_llm(tm_result, llm_result)
    print("Décision finale :", final_decision)

    arduino = ArduinoClient(port="COM3")  # adapter mn b3d
    arduino.send_state(final_decision["label_final"])
    print("Signal envoyé à Arduino")

    db = SQLiteRepository()
    db.insert_log(
        transcript=clean_text,
        score_tm=tm_result["score_tm"],
        score_llm=llm_result["score_llm"],
        score_final=final_decision["score_final"],
        label_final=final_decision["label_final"],
        justification=final_decision["reason_final"]
    )

    print("Log enregistré dans SQLite.")