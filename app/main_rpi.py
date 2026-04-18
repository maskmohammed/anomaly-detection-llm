from gpiozero import Button, LED
from signal import pause
import threading
import time

from app.web.routes import app, start_audio_monitor, refresh_from_db, run_pipeline_job
from app.web.live_state import live_state

button = Button(17, pull_up=True, bounce_time=0.1)
led = LED(18)


def sync_led_forever():
    previous_status = None

    while True:
        state = live_state.get()
        led_status = state.get("led_status", "OFF")

        if led_status != previous_status:
            if led_status == "ON":
                led.on()
            else:
                led.off()
            previous_status = led_status

        time.sleep(0.1)


def handle_physical_button():
    result = run_pipeline_job(source="GPIO")
    if not result.get("ok"):
        print("⚠️", result.get("message", "Erreur inconnue"))


def on_button_pressed():
    threading.Thread(target=handle_physical_button, daemon=True).start()


def start_web_server():
    live_state.update(
        system_status="ACTIF",
        mode="RASPBERRY SYNC + LLM",
        pipeline_state="PRÊT"
    )

    start_audio_monitor()
    refresh_from_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )


if __name__ == "__main__":
    led.off()

    live_state.update(
        system_status="ACTIF",
        mode="RASPBERRY SYNC + LLM",
        pipeline_state="PRÊT",
        led_status="OFF"
    )

    threading.Thread(target=sync_led_forever, daemon=True).start()
    threading.Thread(target=start_web_server, daemon=True).start()

    button.when_pressed = on_button_pressed

    print("👉 Mode Raspberry synchronisé + LLM prêt")
    print("👉 Bouton physique + interface web synchronisés")
    print("👉 Ouvre l’interface sur : http://adresse_du_raspberry:5000")

    pause()