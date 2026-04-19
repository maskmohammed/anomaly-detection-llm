from datetime import datetime
from flask import Flask, render_template, Response, jsonify
from app.database.repository import SQLiteRepository
from app.web.live_state import live_state

import json
import threading
import time
import numpy as np
import sounddevice as sd

app = Flask(__name__)

audio_started = False
audio_lock = threading.Lock()
pipeline_busy = False
pipeline_lock = threading.Lock()


def clamp_percent(value):
    try:
        v = float(value)
        if v <= 1:
            v *= 100
        return max(0, min(100, round(v, 2)))
    except Exception:
        return 0


def build_points(values, width=280, height=100, x_start=20, y_start=20):
    if not values:
        return ""

    vals = [float(v) for v in values]
    vmin = min(vals)
    vmax = max(vals)
    vrange = (vmax - vmin) if vmax != vmin else 1

    points = []
    for i, v in enumerate(vals):
        x = x_start + (i * 35)
        y = y_start + height - (((v - vmin) / vrange) * (height - 10)) - 5
        points.append(f"{x},{round(y, 2)}")
    return " ".join(points)


def refresh_from_db():
    db = SQLiteRepository()
    logs = db.get_last_logs(limit=10)
    latest_log = logs[0] if logs else None

    if latest_log:
        transcript = latest_log[2] or ""
        score_tm = float(latest_log[3] or 0)
        score_llm = float(latest_log[4] or 0)
        score_final = float(latest_log[5] or 0)
        alert_label = latest_log[6] or "NORMAL"
    else:
        transcript = ""
        score_tm = 0
        score_llm = 0
        score_final = 0
        alert_label = "NORMAL"

    keywords = []
    if transcript:
        raw_words = transcript.split()
        cleaned = []
        for w in raw_words:
            w = w.strip(".,;:!?\"'()[]{}").lower()
            if len(w) > 4 and w not in cleaned:
                cleaned.append(w)
        keywords = cleaned[:3]

    recent = list(reversed(logs[:8]))

    normal_series = []
    urgent_series = []
    chart_labels = []

    for log in recent:
        label = log[6] or "NORMAL"
        score = float(log[5] or 0)
        hour_text = str(log[1])[-8:-3] if log[1] else "--:--"
        chart_labels.append(hour_text)

        if label in ["URGENT", "CRITIQUE"]:
            urgent_series.append(score)
            normal_series.append(0)
        else:
            normal_series.append(score)
            urgent_series.append(0)

    while len(chart_labels) < 8:
        chart_labels.insert(0, "--:--")
        normal_series.insert(0, 0)
        urgent_series.insert(0, 0)

    urgent_count = sum(1 for log in logs if (log[6] or "") in ["URGENT", "CRITIQUE"])
    led_status = "ON" if alert_label in ["URGENT", "CRITIQUE"] else "OFF"

    current_state = live_state.get()

    live_state.update(
        system_status="ACTIF",
        mode=current_state.get("mode", "MONITORING"),
        transcript=transcript,
        keywords=keywords,
        score_tm=round(score_tm, 2),
        score_llm=round(score_llm, 2),
        score_final=round(score_final, 2),
        score_tm_percent=clamp_percent(score_tm),
        score_llm_percent=clamp_percent(score_llm),
        score_final_percent=clamp_percent(score_final),
        alert_label=alert_label,
        led_status=led_status,
        urgent_count=urgent_count,
        logs=logs,
        chart_labels=chart_labels,
        normal_points=build_points(normal_series),
        urgent_points=build_points(urgent_series),
        current_time=datetime.now().strftime("%H:%M:%S"),
    )


def start_audio_monitor():
    global audio_started

    with audio_lock:
        if audio_started:
            return
        audio_started = True

    def audio_callback(indata, frames, time_info, status):
        try:
            samples = np.abs(indata[:, 0])
            if len(samples) == 0:
                bars = [8] * 32
            else:
                chunk_size = max(1, len(samples) // 32)
                bars = []
                for i in range(32):
                    start = i * chunk_size
                    end = min(len(samples), start + chunk_size)
                    chunk = samples[start:end]
                    amp = float(np.mean(chunk)) if len(chunk) else 0.0
                    height = int(8 + min(62, amp * 900))
                    bars.append(height)

            live_state.update(waveform=bars)
        except Exception:
            pass

    def worker():
        try:
            with sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=16000,
                blocksize=1024
            ):
                while True:
                    time.sleep(0.1)
        except Exception as e:
            print("Erreur audio monitor :", e)

    threading.Thread(target=worker, daemon=True).start()


# def run_pipeline_job(source="WEB"):
#     global pipeline_busy

#     with pipeline_lock:
#         if pipeline_busy:
#             return {"ok": False, "message": "Pipeline occupé"}
#         pipeline_busy = True

#     try:
#         from app.audio.recorder import record_audio
#         from app.stt.vosk_transcriber import VoskTranscriber
#         from app.text_processing.preprocessor import TextPreprocessor
#         from app.text_mining.engine import TextMiningEngine
#         from app.llm.classifier import LLMClassifier
#         from app.decision.engine import DecisionEngine
#         from app.database.repository import SQLiteRepository

#         current_mode = live_state.get().get("mode", "MONITORING")

#         live_state.update(
#             system_status="ACTIF",
#             mode=current_mode,
#             pipeline_state="ENREGISTREMENT",
#             transcript="",
#             keywords=[],
#         )

#         record_audio("data/test.wav")

#         live_state.update(pipeline_state="TRANSCRIPTION")

#         transcriber = VoskTranscriber()
#         raw_text = transcriber.transcribe("data/test.wav")

#         preprocessor = TextPreprocessor()
#         clean_text = preprocessor.clean(raw_text)

#         live_state.update(
#             pipeline_state="ANALYSE",
#             transcript=clean_text or "",
#         )

#         if not clean_text.strip():
#             live_state.update(
#                 pipeline_state="PRÊT",
#                 transcript="",
#                 keywords=[],
#                 score_tm=0.0,
#                 score_llm=0.0,
#                 score_final=0.0,
#                 score_tm_percent=0.0,
#                 score_llm_percent=0.0,
#                 score_final_percent=0.0,
#                 alert_label="NORMAL",
#                 led_status="OFF",
#             )
#             refresh_from_db()
#             return {"ok": True, "label": "NORMAL", "score": 0.0, "message": "Texte vide"}

#         tm_engine = TextMiningEngine()
#         tm_result = tm_engine.score(clean_text)

#         llm_classifier = LLMClassifier()
#         llm_result = llm_classifier.classify(clean_text)

#         decision_engine = DecisionEngine()
#         final_decision = decision_engine.fuse_tm_llm(tm_result, llm_result)

#         score_tm = float(tm_result.get("score_tm", 0))
#         score_llm = float(llm_result.get("score_llm", 0))
#         score_final = float(final_decision.get("score_final", 0))
#         label = final_decision.get("label_final", "NORMAL")
#         reason = final_decision.get("reason_final", f"Déclenché depuis {source}")

#         db = SQLiteRepository()
#         db.insert_log(
#             transcript=clean_text,
#             score_tm=score_tm,
#             score_llm=score_llm,
#             score_final=score_final,
#             label_final=label,
#             justification=reason
#         )

#         live_state.update(
#             pipeline_state=label,
#             transcript=clean_text,
#             keywords=tm_result.get("keywords", [])[:3],
#             score_tm=round(score_tm, 2),
#             score_llm=round(score_llm, 2),
#             score_final=round(score_final, 2),
#             score_tm_percent=clamp_percent(score_tm),
#             score_llm_percent=clamp_percent(score_llm),
#             score_final_percent=clamp_percent(score_final),
#             alert_label=label,
#             led_status="ON" if label in ["URGENT", "CRITIQUE"] else "OFF",
#         )

#         refresh_from_db()
#         time.sleep(1.2)
#         live_state.update(pipeline_state="PRÊT")

#         return {
#             "ok": True,
#             "label": label,
#             "score": round(score_final, 2),
#             "message": "Traitement terminé"
#         }

#     except Exception as e:
#         live_state.update(
#             pipeline_state="ERREUR",
#             system_status="ACTIF"
#         )
#         print("Erreur pipeline realtime :", e)
#         return {"ok": False, "message": str(e)}

#     finally:
#         with pipeline_lock:
#             pipeline_busy = False

def run_pipeline_job(source="WEB"):
    global pipeline_busy

    with pipeline_lock:
        if pipeline_busy:
            return {"ok": False, "message": "Pipeline occupé"}
        pipeline_busy = True

    try:
        from app.audio.recorder import record_audio
        from app.stt.vosk_transcriber import VoskTranscriber
        from app.text_processing.preprocessor import TextPreprocessor
        from app.text_mining.engine import TextMiningEngine
        # from app.llm.classifier import LLMClassifier
        # from app.decision.engine import DecisionEngine
        from app.database.repository import SQLiteRepository

        current_mode = live_state.get().get("mode", "MONITORING")

        live_state.update(
            system_status="ACTIF",
            mode=current_mode,
            pipeline_state="ENREGISTREMENT",
            transcript="",
            keywords=[],
        )

        record_audio("data/test.wav")

        live_state.update(pipeline_state="TRANSCRIPTION")

        transcriber = VoskTranscriber()
        raw_text = transcriber.transcribe("data/test.wav")

        preprocessor = TextPreprocessor()
        clean_text = preprocessor.clean(raw_text)

        live_state.update(
            pipeline_state="ANALYSE",
            transcript=clean_text or "",
        )

        if not clean_text.strip():
            live_state.update(
                pipeline_state="PRÊT",
                transcript="",
                keywords=[],
                score_tm=0.0,
                score_llm=0.0,
                score_final=0.0,
                score_tm_percent=0.0,
                score_llm_percent=0.0,
                score_final_percent=0.0,
                alert_label="NORMAL",
                led_status="OFF",
            )
            refresh_from_db()
            return {"ok": True, "label": "NORMAL", "score": 0.0, "message": "Texte vide"}

        tm_engine = TextMiningEngine()
        tm_result = tm_engine.score(clean_text)

        score_tm = float(tm_result.get("score_tm", 0))
        score_llm = 0.0

        if score_tm < 50:
            label = "NORMAL"
        elif score_tm < 72:
            label = "URGENT"
        else:
            label = "CRITIQUE"

        score_final = score_tm
        reason = f"Text Mining only depuis {source}"

        db = SQLiteRepository()
        db.insert_log(
            transcript=clean_text,
            score_tm=score_tm,
            score_llm=score_llm,
            score_final=score_final,
            label_final=label,
            justification=reason
        )

        live_state.update(
            pipeline_state=label,
            transcript=clean_text,
            keywords=tm_result.get("keywords", [])[:3],
            score_tm=round(score_tm, 2),
            score_llm=round(score_llm, 2),
            score_final=round(score_final, 2),
            score_tm_percent=clamp_percent(score_tm),
            score_llm_percent=clamp_percent(score_llm),
            score_final_percent=clamp_percent(score_final),
            alert_label=label,
            led_status="ON" if label in ["URGENT", "CRITIQUE"] else "OFF",
        )

        refresh_from_db()
        time.sleep(1.2)
        live_state.update(pipeline_state="PRÊT")

        return {
            "ok": True,
            "label": label,
            "score": round(score_final, 2),
            "message": "Traitement terminé"
        }

    except Exception as e:
        live_state.update(
            pipeline_state="ERREUR",
            system_status="ACTIF"
        )
        print("Erreur pipeline realtime :", e)
        return {"ok": False, "message": str(e)}

    finally:
        with pipeline_lock:
            pipeline_busy = False


@app.route("/events")
def events():
    def generate():
        while True:
            payload = live_state.get()
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            time.sleep(0.35)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/push-to-talk", methods=["POST"])
def push_to_talk():
    with pipeline_lock:
        if pipeline_busy:
            return jsonify({"ok": False, "message": "Pipeline occupé"}), 409

    threading.Thread(target=run_pipeline_job, args=("WEB",), daemon=True).start()
    return jsonify({"ok": True})


@app.route("/")
def index():
    start_audio_monitor()
    refresh_from_db()
    state = live_state.get()

    return render_template(
        "index.html",
        current_time=state["current_time"],
        waveform=state["waveform"],
        latest_log=state["logs"][0] if state["logs"] else None,
        keywords=state["keywords"],
        logs=state["logs"],
        score_tm=f"{state['score_tm']:.2f}",
        score_llm=f"{state['score_llm']:.2f}",
        score_final=f"{state['score_final']:.2f}",
        score_tm_percent=state["score_tm_percent"],
        score_llm_percent=state["score_llm_percent"],
        score_final_percent=state["score_final_percent"],
        alert_label=state["alert_label"],
        urgent_count=state["urgent_count"],
        normal_points=state["normal_points"],
        urgent_points=state["urgent_points"],
        chart_labels=state["chart_labels"],
        pipeline_state=state["pipeline_state"],
        led_status=state["led_status"],
        transcript=state["transcript"],
    )


if __name__ == "__main__":
    start_audio_monitor()
    refresh_from_db()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True, use_reloader=False)