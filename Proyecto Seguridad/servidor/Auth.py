# =========================
# MÓDULOS
# =========================

# Manejo de archivos y rutas
import os

# Lectura y escritura de JSON
import json

# Hash seguro para contraseñas
import bcrypt


# =========================
# RUTA DEL ARCHIVO
# =========================

# Ruta donde se guardarán los usuarios
Listado_USUARIOS = os.path.join(
    os.path.dirname(__file__),
    "usuarios.json"
)


# =========================
# CREAR JSON
# =========================

# Crear archivo si no existe
if not os.path.exists(Listado_USUARIOS):

    with open(Listado_USUARIOS, "w") as f:
        json.dump({}, f)


# =========================
# SANITIZACIÓN
# =========================

def sanitizar_texto(texto, limite=64):
    """
    Limpia y valida textos recibidos.
    """

    if not isinstance(texto, str):
        return None

    texto = texto.strip()

    texto = texto[:limite]

    texto = texto.replace("\n", "")
    texto = texto.replace("\r", "")
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
# FUNCIONES JSON
# =========================

def cargar_usuarios():
    """
    Carga usuarios desde el archivo JSON.
    """

    try:

        with open(Listado_USUARIOS, "r") as f:

            data = json.load(f)

            # Verificar formato válido
            if not isinstance(data, dict):
                return {}

            return data

    except:

        return {}


def guardar_usuarios(data):
    """
    Guarda usuarios en el archivo JSON.
    """

    try:

        with open(Listado_USUARIOS, "w") as f:

            json.dump(
                data,
                f,
                indent=4
            )

    except:

        return False

    return True


# =========================
# REGISTER
# =========================

def registrar_usuario(usuario, password):
    """
    Registra un nuevo usuario.
    """

    usuario = sanitizar_usuario(usuario)

    password = sanitizar_texto(
        password,
        64
    )

    if not usuario:
        return False, "INVALIDUSER"

    if not password:
        return False, "INVALIDPASSWORD"

    usuarios = cargar_usuarios()

    # Verificar si el usuario existe
    if usuario in usuarios:
        return False, "USEREXISTS"

    # Validaciones básicas
    if len(usuario) < 3:
        return False, "INVALIDUSER"

    if len(password) < 6:
        return False, "WEAKPASSWORD"

    try:

        # Generar hash seguro
        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    except:

        return False, "HASHERROR"

    # Guardar usuario
    usuarios[usuario] = password_hash

    if not guardar_usuarios(usuarios):
        return False, "SAVEERROR"

    return True, "REGISTEROK"


# =========================
# LOGIN
# =========================

def login_usuario(usuario, password):
    """
    Verifica credenciales de usuario.
    """

    usuario = sanitizar_usuario(usuario)

    password = sanitizar_texto(
        password,
        64
    )

    if not usuario:
        return False, "INVALIDUSER"

    if not password:
        return False, "INVALIDPASSWORD"

    usuarios = cargar_usuarios()

    # Verificar existencia del usuario
    if usuario not in usuarios:
        return False, "NOUSER"

    hash_guardado = usuarios[usuario]

    try:

        # Comparar contraseña con hash
        valido = bcrypt.checkpw(
            password.encode(),
            hash_guardado.encode()
        )

    except:

        return False, "HASHERROR"

    if valido:
        return True, "LOGINOK"

    return False, "WRONGPASSWORD"