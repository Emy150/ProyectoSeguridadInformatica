import os
os.system("")
import socket
import threading
import datetime
import sys

RESET = "\033[0m"
color_map = {}
usuarios_actuales = []

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
puerto = 55555

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d | %H:%M")

def colorize_message(mensaje):
    if mensaje.startswith("PRIV:"):
        _, contenido = mensaje.split(":", 1)
        remitente_destino, texto = contenido.split(":", 1)
        remitente, destino = remitente_destino.split("->")
        color_remitente = color_map.get(remitente, "")
        color_destino = color_map.get(destino, "")
        return f"[{timestamp()}] {color_remitente}{remitente}{RESET} → {color_destino}{destino}{RESET}: {texto}"

    if ": " in mensaje:
        nombre, resto = mensaje.split(": ", 1)
        color = color_map.get(nombre, "")
        return f"[{timestamp()}] {color}{nombre}{RESET} (global): {resto}"

    parts = mensaje.split(" ", 1)
    if len(parts) == 2:
        nombre, resto = parts
        color = color_map.get(nombre, "")
        return f"[{timestamp()}] {color}{nombre}{RESET} {resto}"

    return f"[{timestamp()}] {mensaje}"

def conectar_con_nombre():
    while True:
        usuario = input("Elige un nombre de usuario: ").strip()
        if not usuario:
            print("El nombre de usuario no puede estar vacío.")
            continue

        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            cliente.connect((host, puerto))
        except:
            print("No se pudo conectar al servidor.")
            continue

        cliente.send(usuario.encode("utf-8"))

        try:
            respuesta = cliente.recv(1024).decode("utf-8")
        except:
            cliente.close()
            continue

        if respuesta == "NAMEINUSE":
            print("Ese nombre ya está en uso.")
        elif respuesta == "CHATFULL":
            print("El chat está lleno.")
        elif respuesta == "INVALIDNAME":
            print("Nombre inválido.")
        elif respuesta == "OK":
            print(f"Bienvenido {usuario}!")
            return cliente, usuario

        cliente.close()

cliente, usuario = conectar_con_nombre()

def recibir():
    buffer = ""
    global usuarios_actuales

    while True:
        try:
            data = cliente.recv(1024).decode("utf-8")
            if not data:
                raise Exception()

            buffer += data
            while "ENDMSG" in buffer:
                mensaje, buffer = buffer.split("ENDMSG", 1)
                mensaje = mensaje.strip()

                if mensaje.startswith("ASSIGNCOLOR:"):
                    _, nombre, color = mensaje.split(":", 2)
                    color_map[nombre] = color
                    continue

                if mensaje.startswith("REMOVEUSER:"):
                    _, nombre = mensaje.split(":", 1)
                    color_map.pop(nombre, None)
                    continue

                if mensaje.startswith("USERLIST:"):
                    _, lista = mensaje.split(":", 1)
                    usuarios_actuales = lista.split(",") if lista else []
                    continue

                print(colorize_message(mensaje))

        except:
            print("Conexión perdida con el servidor.")
            cliente.close()
            break

def escribir():
    while True:
        try:
            texto = input("")
            if texto.strip() == "":
                continue

            if texto.startswith("@"):
                mensaje = texto
            else:
                mensaje = f"{usuario}: {texto}"

            cliente.send(mensaje.encode("utf-8"))
        except:
            cliente.close()
            break

threading.Thread(target=recibir, daemon=True).start()
threading.Thread(target=escribir, daemon=True).start()

while True:
    try:
        threading.Event().wait(1)
    except KeyboardInterrupt:
        cliente.close()
        break
