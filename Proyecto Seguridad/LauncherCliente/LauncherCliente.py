import socket
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent

CLIENT_FILE = HERE / "cliente" / "Cliente_tcp.py"

def check_files():
    if not CLIENT_FILE.exists():
        print("Falta el archivo:")
        print("   ", CLIENT_FILE)
        sys.exit(1)

def which_term_linux():
    candidates = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]

    for c in candidates:
        if shutil.which(c):
            return c

    return None

def open_terminal_and_run(args):
    system = platform.system()

    # WINDOWS
    if system == "Windows":
        subprocess.Popen(
            args,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return

    # MAC
    if system == "Darwin":
        subprocess.Popen(
            ["open", "-a", "Terminal.app"] + args
        )
        return

    # LINUX
    term = which_term_linux()

    if term:
        subprocess.Popen([term, "--"] + args)
        return

    subprocess.Popen(args)

def start_clients(server_ip, n, python_exec=sys.executable):
    for i in range(n):

        args = [
            python_exec,
            str(CLIENT_FILE),
            server_ip
        ]

        print(f"Abrir cliente #{i+1} → {server_ip}")

        open_terminal_and_run(args)

        time.sleep(0.4)

def main():
    check_files()

    python_exec = sys.executable

    server_ip = input("Ingresa la IP del servidor: ").strip()

    try:
        cantidad = int(
            input("¿Cuántos clientes deseas abrir?: ").strip()
        )

        if cantidad < 1:
            raise ValueError

    except ValueError:
        print("Número inválido.")
        return

    print(f"\nConectando {cantidad} cliente(s) por TCP a {server_ip}...\n")

    start_clients(server_ip, cantidad, python_exec)

    print("\nClientes lanzados correctamente.")

if __name__ == "__main__":
    main()