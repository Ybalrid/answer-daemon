#!/usr/bin/env python3

import os
import socket
import threading
import serial
import time

SERIAL_PORT = "/dev/ttyUSB0"
SOCKET_PATH = "/tmp/answer-daemon.sock"


ser = serial.Serial(
    SERIAL_PORT,
    baudrate=115200,
    bytesize=8,
    parity="N",
    stopbits=1,
    rtscts=True,
    timeout=0.2,
)


def modem_reader():
    """Affiche en permanence ce que raconte l'Olitec."""
    while True:
        data = ser.read(1024)
        if data:
            print(data.decode(errors="replace"),
                end="",
                flush=True,
            )


threading.Thread(target=modem_reader, daemon=True).start()


if os.path.exists(SOCKET_PATH):
    os.unlink(SOCKET_PATH)

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(SOCKET_PATH)

# Prototype : permet à l'utilisateur asterisk d'y accéder.
# On sécurisera ça proprement avec groupe + systemd ensuite.
os.chmod(SOCKET_PATH, 0o666)

sock.listen(5)

print(f"Serial ouvert : {SERIAL_PORT}")
print(f"Socket : {SOCKET_PATH}")
print("En attente de commandes...")

try:
    while True:
        conn, _ = sock.accept()

        with conn:
            command = conn.recv(1024).decode().strip().upper()
            print(f"[COMMAND] {command}")

            if command == "ANSWER":
                print("[ACTION] ATA")
                ser.write(b"ATA\r")
                ser.flush()
                conn.sendall(b"OK\n")

            elif command == "AT":
                ser.write(b"AT\r")
                ser.flush()
                conn.sendall(b"OK\n")

            elif command == "HANGUP":
                print("[ACTION] DTR down -> hangup")
                ser.dtr = False
                time.sleep(0.2)
                ser.dtr = True
                conn.sendall(b"OK\n")

            else:
                print(f"[WARN] commande inconnue : {command}")
                conn.sendall(b"ERROR\n")

finally:
    sock.close()
    ser.close()

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)
