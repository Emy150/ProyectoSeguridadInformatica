import os
os.system("")
import threading
import socket
import datetime

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

host = "0.0.0.0"
ip_mostrar = obtener_ip_local()
puerto = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, puerto))

server.listen()

clientes = []
usuarios = []
colores_usuarios = {}

COLORES = [
    "\033[38;5;81m",
    "\033[38;5;141m",
    "\033[38;5;75m",
    "\033[38;5;120m",
    "\033[38;5;229m",
]

RESET = "\033[0m"

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d | %H:%M")

def log_event(evento):
    print(f"[{timestamp()}] {evento}")

def broadcast(mensaje):
    if isinstance(mensaje, str):
        mensaje = mensaje.encode("utf-8")
    mensaje += b"\nENDMSG\n"
    for cliente in clientes:
        try:
            cliente.send(mensaje)
        except:
            pass

def enviar_lista_usuarios():
    lista = ",".join(usuarios)
    broadcast(f"USERLIST:{lista}")

def handle(cliente):
    while True:
        try:
            mensaje = cliente.recv(1024)
            if not mensaje:
                raise Exception("socket closed")

            mensaje = mensaje.decode("utf-8")

            if mensaje.startswith("@"):
                try:
                    destino, texto = mensaje[1:].split(" ", 1)
                except ValueError:
                    continue
                if destino in usuarios:
                    idx_dest = usuarios.index(destino)
                    idx_rem = clientes.index(cliente)
                    remitente = usuarios[idx_rem]
                    clientes[idx_dest].send(f"PRIV:{remitente}->{destino}:{texto}".encode("utf-8") + b"\nENDMSG\n")
                    cliente.send(f"PRIV:{remitente}->{destino}:{texto}".encode("utf-8") + b"\nENDMSG\n")
                    log_event(f"Mensaje privado: {remitente} → {destino}: {texto}")
                continue

            broadcast(mensaje)
            log_event(f"Mensaje global: {mensaje}")

        except:
            if cliente in clientes:
                index = clientes.index(cliente)
                usuario = usuarios[index]

                clientes.remove(cliente)
                cliente.close()
                usuarios.remove(usuario)
                colores_usuarios.pop(usuario, None)

                broadcast(f"REMOVEUSER:{usuario}")
                broadcast(f"{usuario} salió del chat")
                enviar_lista_usuarios()

                log_event(f"{usuario} desconectado del chat")
            break

def receive():
    log_event(f"Servidor TCP escuchando en {ip_mostrar}:{puerto}")

    while True:
        cliente, direccion = server.accept()
        log_event(f"Nuevo cliente intentando conectar: {direccion}")

        if len(clientes) >= 5:
            cliente.send("CHATFULL".encode("utf-8"))
            cliente.close()
            log_event(f"Intento de conexión rechazado (chat lleno) desde {direccion}")
            continue

        try:
            usuario = cliente.recv(1024).decode("utf-8").strip()
        except:
            cliente.close()
            continue

        if not usuario:
            cliente.send("INVALIDNAME".encode("utf-8"))
            cliente.close()
            log_event(f"Intento de conexión rechazado (nombre vacío) desde {direccion}")
            continue

        if usuario in usuarios:
            cliente.send("NAMEINUSE".encode("utf-8"))
            cliente.close()
            log_event(f"Intento de conexión rechazado (nombre duplicado): {usuario}")
            continue

        cliente.send("OK".encode("utf-8"))
        usuarios.append(usuario)
        clientes.append(cliente)
        color = COLORES[(len(usuarios)-1) % len(COLORES)]
        colores_usuarios[usuario] = color

        broadcast(f"ASSIGNCOLOR:{usuario}:{color}")
        broadcast(f"{usuario} se unió al chat")
        enviar_lista_usuarios()
        log_event(f"{usuario} se unió al chat desde {direccion}")

        threading.Thread(target=handle, args=(cliente,), daemon=True).start()

try:
    receive()
except KeyboardInterrupt:
    print("\nServidor detenido correctamente.")
    server.close()
