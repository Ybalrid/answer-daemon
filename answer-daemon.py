#!/usr/bin/env python3


import os
import socket
import threading
import serial
import time

SERIAL_PORT = "/dev/ttyUSB0"
SOCKET_PATH = "/tmp/answer-daemon.sock"


# Relais telnet pour BBS
BBS_HOST = "127.0.0.1"
BBS_PORT = 2323

bbs_sock = None
data_mode = False

def connect_bbs():
    global bbs_sock

    print(f"[BBS] connexion à {BBS_HOST}:{BBS_PORT}")
    bbs_sock = socket.create_connection((BBS_HOST, BBS_PORT))
    print("[BBS] connecté à Mystic")

    threading.Thread(
        target=bbs_reader,
        daemon=True,
    ).start()

def bbs_reader():
    global bbs_sock, data_mode

    try:
        while data_mode:
            data = bbs_sock.recv(4096)

            if not data:
                print("[BBS] Mystic a fermé la connexion")
                break

            ser.write(data)
            ser.flush()

    finally:
        if bbs_sock:
            bbs_sock.close()
            bbs_sock = None

        data_mode = False


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
    global data_mode

    line_buffer = b""

    while True:
        data = ser.read(1024)

        if not data:
            continue

        if data_mode:
            if bbs_sock:
                bbs_sock.sendall(data)

            continue

        # Mode commandes modem
        print(
            data.decode(errors="replace"),
            end="",
            flush=True,
        )

        line_buffer += data

        while b"\n" in line_buffer:
            line, line_buffer = line_buffer.split(b"\n", 1)
            line = line.strip()

            if line.startswith(b"CONNECT"):
                print("\n[MODEM] DATA MODE")

                data_mode = True
                connect_bbs()
                break

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
                time.sleep(1.0)
                ser.dtr = True
                try:
                    conn.sendall(b"OK\n")
                except BrokenPipeError:
                    pass

            else:
                print(f"[WARN] commande inconnue : {command}")
                conn.sendall(b"ERROR\n")

finally:
    sock.close()
    ser.close()

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)
