import serial
import time


class ArduinoClient:
    def __init__(self, port="COM3", baudrate=9600):
        self.ser = serial.Serial(port, baudrate)
        time.sleep(2)

    def send_state(self, label: str):
        if label == "NORMAL":
            self.ser.write(b'0')
        elif label == "URGENT":
            self.ser.write(b'1')
        elif label == "CRITIQUE":
            self.ser.write(b'2')