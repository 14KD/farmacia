import hashlib


# =========================================
# ENCRIPTAR CONTRASEÑA
# =========================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# =========================================
# VERIFICAR CONTRASEÑA
# =========================================

def verify_password(
    password,
    hashed_password
):

    return hash_password(password) == hashed_password