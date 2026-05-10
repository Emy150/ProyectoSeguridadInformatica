import os
import json
import bcrypt

# Ajustar la ruta del archivo usuarios.json a la carpeta Usuarios
USUARIOS_DIR = os.path.join(os.path.dirname(__file__), "Usuarios")
Listado_USUARIOS = os.path.join(
    os.path.dirname(__file__),
    "usuarios.json"
)

# Crear archivo si no existe
if not os.path.exists(Listado_USUARIOS):
    try:
        with open(Listado_USUARIOS, "w") as f:
            json.dump({}, f)
    except PermissionError:
        print(f"Error: No se pudo crear el archivo {Listado_USUARIOS} debido a permisos insuficientes.")
        raise

def cargar_usuarios():
    try:
        with open(Listado_USUARIOS, "r") as f:
            return json.load(f)
    except PermissionError:
        print(f"Error: No se pudo leer el archivo {Listado_USUARIOS} debido a permisos insuficientes.")
        raise

def guardar_usuarios(data):
    try:
        with open(Listado_USUARIOS, "w") as f:
            json.dump(data, f, indent=4)
    except PermissionError:
        print(f"Error: No se pudo escribir en el archivo {Listado_USUARIOS} debido a permisos insuficientes.")
        raise

def registrar_usuario(usuario, password):

    usuarios = cargar_usuarios()

    # Usuario ya existe
    if usuario in usuarios:
        return False, "USEREXISTS"

    # Validaciones
    if len(usuario) < 3:
        return False, "INVALIDUSER"

    if len(password) < 6:
        return False, "WEAKPASSWORD"

    # Hash
    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    usuarios[usuario] = password_hash

    guardar_usuarios(usuarios)

    return True, "REGISTEROK"


def login_usuario(usuario, password):

    usuarios = cargar_usuarios()

    if usuario not in usuarios:
        return False, "NOUSER"

    hash_guardado = usuarios[usuario]

    valido = bcrypt.checkpw(
        password.encode(),
        hash_guardado.encode()
    )

    if valido:
        return True, "LOGINOK"

    return False, "WRONGPASSWORD"