# =========================
# MÓDULOS
# =========================

# Ejecutar comandos del sistema
import os
os.system("")
import rsa
import base64
# Conexión TCP/IP
import socket

# Manejo de hilos
import threading

# Fechas y horas
import datetime

# Argumentos de consola
import sys


# =========================
# VARIABLES
# =========================

# Reset de color ANSI
RESET = "\033[0m"

# Diccionario usuario-color
color_map = {}

# Lista de usuarios conectados
usuarios_actuales = []

# Host recibido por consola
host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

# Puerto del servidor
puerto = 55555

cliente_pub_key = None
cliente_priv_key = None
server_pub_key = None
# =========================
# SEGURIDAD
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

    permitido = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_"
    )

    for c in usuario:
        if c not in permitido:
            return None

    return usuario


# =========================
# FUNCIONES AUXILIARES
# =========================

def timestamp():
    """
    Devuelve fecha y hora actual.
    """

    return datetime.datetime.now().strftime("%Y-%m-%d | %H:%M")


def colorize_message(mensaje):
    """
    Agrega colores y formato a mensajes.
    """

    # Mensajes privados
    if mensaje.startswith("PRIV:"):

        _, contenido = mensaje.split(":", 1)

        remitente_destino, texto = contenido.split(":", 1)

        remitente, destino = remitente_destino.split("->")

        color_remitente = color_map.get(remitente, "")

        color_destino = color_map.get(destino, "")

        return (
            f"[{timestamp()}] "
            f"{color_remitente}{remitente}{RESET} "
            f"→ "
            f"{color_destino}{destino}{RESET}: "
            f"{texto}"
        )

    # Mensajes globales
    if ": " in mensaje:

        nombre, resto = mensaje.split(": ", 1)

        color = color_map.get(nombre, "")

        return (
            f"[{timestamp()}] "
            f"{color}{nombre}{RESET} "
            f"(global): {resto}"
        )

    # Mensajes generales
    parts = mensaje.split(" ", 1)

    if len(parts) == 2:

        nombre, resto = parts

        color = color_map.get(nombre, "")

        return (
            f"[{timestamp()}] "
            f"{color}{nombre}{RESET} "
            f"{resto}"
        )

    return f"[{timestamp()}] {mensaje}"


# =========================
# AUTENTICACIÓN
# =========================

def autenticar():
    """
    Maneja login y registro de usuarios.
    """
    global cliente_pub_key, cliente_priv_key, server_pub_key

    while True:

        print("\n=== AUTENTICACIÓN ===")
        print("[1] Login")
        print("[2] Registrar")
        print("[3] Salir")

        opcion = input("> ").strip()

        if opcion == "3":
            sys.exit()

        if opcion not in ["1", "2"]:
            print("Opción inválida.")
            continue

        usuario = input("Usuario: ")
        password = input("Contraseña: ")

        usuario = sanitizar_usuario(usuario)
        password = sanitizar_texto(password, 64)

        if not usuario or not password:
            print("Datos inválidos.")
            continue

        # Crear socket cliente
        cliente = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        try:

            cliente.connect((host, puerto))

        except:

            print("No se pudo conectar al servidor.")

            continue

        # Login
        if opcion == "1":

            datos = (
                f"LOGIN|{usuario}|{password}"
            )

        # Registro
        else:

            datos = (
                f"REGISTER|{usuario}|{password}"
            )

        try:

            cliente.send(
                datos.encode("utf-8")
            )

        except:

            cliente.close()

            continue

        try:

            respuesta = cliente.recv(1024)

            if len(respuesta) > 1024:
                raise Exception()

            respuesta = respuesta.decode("utf-8")

        except:

            cliente.close()

            continue

        # Respuestas del servidor
        if respuesta == "LOGINOK":

            print("Generando claves RSA (2048 bits)... Por favor espera.")
            cliente_pub_key, cliente_priv_key = rsa.newkeys(2048)
            
            # Enviar clave pública al servidor
            pub_pem = cliente_pub_key.save_pkcs1()
            pub_b64 = base64.b64encode(pub_pem).decode('utf-8')
            cliente.send(f"PUBKEY|{pub_b64}\nENDMSG\n".encode('utf-8'))
            
            # Recibir clave del servidor
            resp = cliente.recv(4096).decode('utf-8')
            if "SERVERPUBKEY|" in resp:
                srv_pem_b64 = resp.split("SERVERPUBKEY|")[1].split("\nENDMSG\n")[0]
                srv_pem = base64.b64decode(srv_pem_b64)
                server_pub_key = rsa.PublicKey.load_pkcs1(srv_pem)
            print("¡Conexión cifrada de extremo a extremo establecida!\n")

            return cliente, usuario

        elif respuesta == "REGISTEROK":

            print("Generando claves RSA (2048 bits)... Por favor espera.")
            cliente_pub_key, cliente_priv_key = rsa.newkeys(2048)
            
            # Enviar clave pública al servidor
            pub_pem = cliente_pub_key.save_pkcs1()
            pub_b64 = base64.b64encode(pub_pem).decode('utf-8')
            cliente.send(f"PUBKEY|{pub_b64}\nENDMSG\n".encode('utf-8'))
            
            # Recibir clave del servidor
            resp = cliente.recv(4096).decode('utf-8')
            if "SERVERPUBKEY|" in resp:
                srv_pem_b64 = resp.split("SERVERPUBKEY|")[1].split("\nENDMSG\n")[0]
                srv_pem = base64.b64decode(srv_pem_b64)
                server_pub_key = rsa.PublicKey.load_pkcs1(srv_pem)
            print("¡Conexión cifrada de extremo a extremo establecida!\n")
            print("Usuario registrado correctamente.")

            print(f"Bienvenido {usuario}!")

            return cliente, usuario

        elif respuesta == "WRONGPASSWORD":

            print("Contraseña incorrecta.")

        elif respuesta == "NOUSER":

            print("Ese usuario no existe.")

        elif respuesta == "USEREXISTS":

            print("Ese usuario ya existe.")

        elif respuesta == "WEAKPASSWORD":

            print("La contraseña es muy débil.")

        elif respuesta == "INVALIDUSER":

            print("Usuario inválido.")

        elif respuesta == "INVALIDDATA":

            print("Datos inválidos.")

        elif respuesta == "NAMEINUSE":

            print("Ese usuario ya está conectado.")

        elif respuesta == "CHATFULL":

            print("El chat está lleno.")

        else:

            print(f"Error: {respuesta}")

        cliente.close()


# =========================
# RECIBIR MENSAJES
# =========================

def recibir():
    """
    Recibe mensajes del servidor.
    """

    buffer = ""

    global usuarios_actuales

    while True:

        try:

            data = cliente.recv(1024)

            if len(data) > 1024:
                raise Exception()

            data = data.decode("utf-8")

            if not data:
                raise Exception()

            buffer += data

            while "ENDMSG" in buffer:
                mensaje_crudo, buffer = buffer.split("ENDMSG", 1)
                mensaje_crudo = mensaje_crudo.strip()
                
                if not mensaje_crudo:
                    continue

                # --- DESCIFRAR MENSAJE ---
                try:
                    msg_bytes = base64.b64decode(mensaje_crudo)
                    mensaje_descifrado = rsa.decrypt(msg_bytes, cliente_priv_key).decode("utf-8")
                    mensaje = sanitizar_texto(mensaje_descifrado)
                except:
                    continue # Si falla el descifrado, ignoramos el paquete

                if not mensaje:
                    continue

                # Asignar color
                if mensaje.startswith("ASSIGNCOLOR:"):

                    _, nombre, color = mensaje.split(
                        ":",
                        2
                    )

                    nombre = sanitizar_usuario(
                        nombre
                    )

                    if nombre:
                        color_map[nombre] = color

                    continue

                # Eliminar usuario
                if mensaje.startswith("REMOVEUSER:"):

                    _, nombre = mensaje.split(
                        ":",
                        1
                    )

                    nombre = sanitizar_usuario(
                        nombre
                    )

                    if nombre:
                        color_map.pop(nombre, None)

                    continue

                # Actualizar lista de usuarios
                if mensaje.startswith("USERLIST:"):

                    _, lista = mensaje.split(
                        ":",
                        1
                    )

                    usuarios_actuales = [
                        sanitizar_usuario(u)
                        for u in lista.split(",")
                        if sanitizar_usuario(u)
                    ]

                    continue

                print(
                    colorize_message(mensaje)
                )

        except:

            print(
                "Conexión perdida con el servidor."
            )

            cliente.close()

            break


# =========================
# ENVIAR MENSAJES
# =========================

def escribir():
    """
    Envía mensajes al servidor.
    """

    while True:

        try:

            texto = input("")

            texto = sanitizar_texto(texto)

            if not texto:
                continue

            # Mensajes privados
            if texto.startswith("@"):

                try:

                    destino, contenido = texto[1:].split(
                        " ",
                        1
                    )

                    destino = sanitizar_usuario(
                        destino
                    )

                    contenido = sanitizar_texto(
                        contenido
                    )

                    if not destino or not contenido:
                        print("Mensaje inválido.")
                        continue

                    mensaje = (
                        f"@{destino} {contenido}"
                    )

                except:

                    print(
                        "Formato privado inválido."
                    )

                    continue

            # Mensajes globales
            else:

                mensaje = (
                    f"{usuario}: {texto}"
                )

            msg_cifrado = rsa.encrypt(mensaje.encode("utf-8"), server_pub_key)
            msg_b64 = base64.b64encode(msg_cifrado).decode("utf-8")
            
            cliente.send((msg_b64 + "\nENDMSG\n").encode("utf-8"))

        except:
            cliente.close()
            break


# =========================
# INICIAR CLIENTE
# =========================

# Login o registro
cliente, usuario = autenticar()

# Hilo para recibir mensajes
threading.Thread(
    target=recibir,
    daemon=True
).start()

# Hilo para escribir mensajes
threading.Thread(
    target=escribir,
    daemon=True
).start()


# Mantener cliente activo
while True:

    try:

        threading.Event().wait(1)

    except KeyboardInterrupt:

        cliente.close()

        break