import socket
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import time

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]

    finally:
        s.close()

    return ip

HERE = Path(__file__).resolve().parent

SERVER_FILE = HERE / "servidor" / "Servidor_tcp.py"
CLIENT_FILE = HERE / "cliente" / "Cliente_tcp.py"

def check_files():

    missing = []

    if not SERVER_FILE.exists():
        missing.append(str(SERVER_FILE))

    if not CLIENT_FILE.exists():
        missing.append(str(CLIENT_FILE))

    if missing:
        print("Faltan archivos:")

        for m in missing:
            print("   ", m)

        sys.exit(1)

def which_term_linux():

    candidates = [
        "gnome-terminal",
        "konsole",
        "xfce4-terminal",
        "xterm",
        "terminator",
        "mate-terminal"
    ]

    for c in candidates:
        if shutil.which(c):
            return c

    return None

def open_terminal_and_run(cmd):

    system = platform.system()

    # WINDOWS
    if system == "Windows":

        full = f'start "ChatClient" cmd /k "{cmd}"'

        return subprocess.Popen(
            full,
            shell=True
        )

    # MAC
    if system == "Darwin":

        apple_command = (
            f'''osascript -e 'tell application "Terminal" '''
            f'''to do script "{cmd}"' '''
        )

        return subprocess.Popen(
            apple_command,
            shell=True
        )

    # LINUX
    term = which_term_linux()

    if term:
        return subprocess.Popen(
            [term, "--", "bash", "-c", f'{cmd}; exec bash']
        )

    return subprocess.Popen(cmd, shell=True)

def start_server(server_path, use_python=sys.executable):

    cmd = f'"{use_python}" "{server_path}"'

    print(f"Iniciando servidor: {cmd}")

    return subprocess.Popen(cmd, shell=True)

def start_clients_in_terminals(
    client_path,
    server_ip,
    python_exec=sys.executable
):

    cmd = f'"{python_exec}" "{client_path}" {server_ip}'

    print(f"Abrir cliente con IP {server_ip}")

    open_terminal_and_run(cmd)

def main():

    check_files()

    auto_clients = input(
        "¿Abrir automáticamente cliente? (s/n) [s]: "
    ).strip().lower()

    if auto_clients == "":
        auto_clients = "s"

    abrir_clientes = auto_clients == "s"

    python_exec = sys.executable

    server_ip = obtener_ip_local()

    print(f"\nServidor TCP levantándose en IP: {server_ip}\n")

    server_proc = start_server(
        SERVER_FILE,
        python_exec
    )

    time.sleep(1.2)

    if abrir_clientes:

        start_clients_in_terminals(
            CLIENT_FILE,
            server_ip,
            python_exec
        )

    print("\nServidor ejecutándose.")
    print("Presiona Ctrl+C para salir del launcher.")

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print(
            "\nLauncher cerrado "
            "(el servidor sigue activo)."
        )

if __name__ == "__main__":
    main()