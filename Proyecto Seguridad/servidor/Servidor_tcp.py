# =========================
# MÓDULOS
# =========================

# Permite ejecutar comandos del sistema
import os
os.system("")
import rsa
import base64
# Manejo de hilos para múltiples clientes
import threading

# Conexiones TCP/IP
import socket

# Fechas y horas
import datetime

# Funciones de autenticación
from Auth import registrar_usuario, login_usuario


# =========================
# FUNCIONES DE SEGURIDAD
# =========================

def sanitizar_texto(texto, limite=200):
    """
    Limpia y valida textos recibidos.
    """

    if not isinstance(texto, str):
        return None

    texto = texto.strip()
    texto = texto[:limite]

    texto = texto.replace("\n", " ")
    texto = texto.replace("\r", " ")
    texto = texto.replace("\0", "")

    return texto


def sanitizar_usuario(usuario):
    """
    Valida nombres de usuario.
    """

    usuario = sanitizar_texto(usuario, 20)

    if not usuario:
        return None

    permitido = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

    for c in usuario:
        if c not in permitido:
            return None

    return usuario


# =========================
# RED
# =========================

def obtener_ip_local():
    """
    Obtiene la IP local del servidor.
    """

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

# Socket principal del servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((host, puerto))

server.listen()


# =========================
# VARIABLES
# =========================

# Clientes conectados
clientes = []

# Usuarios conectados
usuarios = []

# Colores asignados
colores_usuarios = {}

COLORES = [
    "\033[38;5;81m",
    "\033[38;5;141m",
    "\033[38;5;75m",
    "\033[38;5;120m",
    "\033[38;5;229m",
]

RESET = "\033[0m"

print("Generando claves RSA del servidor (2048 bits)...")
server_pub_key, server_priv_key = rsa.newkeys(2048)
claves_clientes = {}

# =========================
# FUNCIONES AUXILIARES
# =========================

def timestamp():
    """
    Devuelve fecha y hora actual.
    """

    return datetime.datetime.now().strftime("%Y-%m-%d | %H:%M")


def log_event(evento):
    """
    Muestra eventos en consola.
    """

    print(f"[{timestamp()}] {evento}")


def broadcast(mensaje):
    """
    Cifra y envía mensajes a todos los clientes usando la clave pública de cada uno.
    """
    if isinstance(mensaje, str):
        mensaje = mensaje.encode("utf-8")

    for i, cliente in enumerate(clientes):
        try:
            usuario = usuarios[i]
            pub_key = claves_clientes.get(usuario)
            
            if pub_key:
                # Cifrar con la clave pública del cliente destino
                msg_cifrado = rsa.encrypt(mensaje, pub_key)
                msg_b64 = base64.b64encode(msg_cifrado)
                cliente.send(msg_b64 + b"\nENDMSG\n")
        except:
            pass


def enviar_lista_usuarios():
    """
    Envía la lista de usuarios conectados.
    """

    lista = ",".join(usuarios)
    broadcast(f"USERLIST:{lista}")


# =========================
# CLIENTES
# =========================

def handle(cliente):
    """
    Maneja mensajes y desconexiones de clientes.
    """

    while True:

        try:
            # Aumentamos el buffer por el tamaño de Base64
            mensaje_crudo = cliente.recv(2048).decode("utf-8")

            if not mensaje_crudo:
                raise Exception("Socket cerrado")

            if "ENDMSG" in mensaje_crudo:
                mensaje_crudo = mensaje_crudo.split("\nENDMSG\n")[0]

            # Descifrar con la clave privada del servidor
            msg_bytes = base64.b64decode(mensaje_crudo)
            mensaje_descifrado = rsa.decrypt(msg_bytes, server_priv_key).decode("utf-8")

            mensaje = sanitizar_texto(mensaje_descifrado)

            if not mensaje:
                continue

            # Mensajes privados
            if mensaje.startswith("@"):

                try:
                    destino, texto = mensaje[1:].split(" ", 1)

                    destino = sanitizar_usuario(destino)
                    texto = sanitizar_texto(texto)

                    if not destino or not texto:
                        continue

                except ValueError:
                    continue

                if destino in usuarios:

                    idx_dest = usuarios.index(destino)
                    idx_rem = clientes.index(cliente)

                    remitente = usuarios[idx_rem]

                    mensaje_privado = (
                        f"PRIV:{remitente}->{destino}:{texto}"
                    )

                    # --- CIFRAR PARA EL DESTINATARIO ---
                    pub_key_dest = claves_clientes.get(destino)
                    if pub_key_dest:
                        msg_cifrado_dest = rsa.encrypt(mensaje_privado.encode("utf-8"), pub_key_dest)
                        clientes[idx_dest].send(base64.b64encode(msg_cifrado_dest) + b"\nENDMSG\n")

                    # --- CIFRAR PARA EL REMITENTE (Para que se vea en su propia consola) ---
                    pub_key_rem = claves_clientes.get(remitente)
                    if pub_key_rem:
                        msg_cifrado_rem = rsa.encrypt(mensaje_privado.encode("utf-8"), pub_key_rem)
                        cliente.send(base64.b64encode(msg_cifrado_rem) + b"\nENDMSG\n")

                    log_event(
                        f"Mensaje privado: {remitente} → {destino}"
                    )

                continue

            # Mensajes globales
            mensaje = sanitizar_texto(mensaje)

            if not mensaje:
                continue

            broadcast(mensaje)

            log_event(f"Mensaje global: {mensaje}")

        except:

            # Desconectar cliente
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

                log_event(f"{usuario} desconectado")

            break


# =========================
# CONEXIONES
# =========================

def receive():
    """
    Acepta conexiones y valida login/register.
    """

    log_event(
        f"Servidor escuchando en {ip_mostrar}:{puerto}"
    )

    while True:

        cliente, direccion = server.accept()

        log_event(
            f"Cliente conectado: {direccion}"
        )

        # Límite de usuarios
        if len(clientes) >= 5:

            cliente.send(
                "CHATFULL".encode("utf-8")
            )

            cliente.close()

            continue

        # Recibir datos
        try:

            datos = cliente.recv(1024)

            if len(datos) > 1024:
                raise Exception()

            datos = datos.decode("utf-8").strip()

            partes = datos.split("|")

            if len(partes) != 3:

                cliente.send(
                    "INVALIDFORMAT".encode("utf-8")
                )

                cliente.close()

                continue

            accion, usuario, password = partes

            accion = sanitizar_texto(accion, 20)

            usuario = sanitizar_usuario(usuario)

            password = sanitizar_texto(password, 64)

            if not accion or not usuario or not password:

                cliente.send(
                    "INVALIDDATA".encode("utf-8")
                )

                cliente.close()

                continue

        except:

            cliente.close()
            continue

        # Usuario repetido
        if usuario in usuarios:

            cliente.send(
                "NAMEINUSE".encode("utf-8")
            )

            cliente.close()

            continue

        # Registro
        if accion == "REGISTER":

            ok, respuesta = registrar_usuario(
                usuario,
                password
            )

            cliente.send(
                respuesta.encode("utf-8")
            )

            if not ok:
                cliente.close()
                continue

        # Login
        elif accion == "LOGIN":

            ok, respuesta = login_usuario(
                usuario,
                password
            )

            cliente.send(
                respuesta.encode("utf-8")
            )

            if not ok:
                cliente.close()
                continue

        # Acción inválida
        else:

            cliente.send(
                "INVALIDACTION".encode("utf-8")
            )

            cliente.close()

            continue

        # Agregar cliente
        usuarios.append(usuario)

        clientes.append(cliente)

        try:
            # Recibir clave pública del cliente
            msg_key = cliente.recv(2048).decode("utf-8")
            if "PUBKEY|" in msg_key:
                pem_b64 = msg_key.split("PUBKEY|")[1].split("\nENDMSG\n")[0]
                claves_clientes[usuario] = rsa.PublicKey.load_pkcs1(base64.b64decode(pem_b64))
                
                # Enviar clave pública del servidor
                srv_pub_b64 = base64.b64encode(server_pub_key.save_pkcs1()).decode('utf-8')
                cliente.send(f"SERVERPUBKEY|{srv_pub_b64}\nENDMSG\n".encode('utf-8'))
        except Exception as e:
            print(f"Error en intercambio de claves con {usuario}: {e}")
            usuarios.remove(usuario)   
            clientes.remove(cliente)   
            cliente.close()
            continue

        color = COLORES[
            (len(usuarios)-1) % len(COLORES)
        ]

        colores_usuarios[usuario] = color

        broadcast(
            f"ASSIGNCOLOR:{usuario}:{color}"
        )

        broadcast(
            f"{usuario} se unió al chat"
        )

        enviar_lista_usuarios()

        log_event(
            f"{usuario} conectado correctamente"
        )

        # Hilo para cliente
        threading.Thread(
            target=handle,
            args=(cliente,),
            daemon=True
        ).start()


# =========================
# INICIAR SERVIDOR
# =========================

try:

    # Ejecutar servidor
    receive()

except KeyboardInterrupt:

    print("\nServidor detenido.")

    server.close()