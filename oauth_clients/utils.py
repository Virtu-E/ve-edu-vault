from base64 import b64decode, b64encode

from cryptography.fernet import Fernet

from edu_vault.settings.common import ENCRYPTION_KEY


def get_encryption_key():
    return Fernet(ENCRYPTION_KEY.encode())


def encrypt_value(value):
    if not value:
        return value
    f = get_encryption_key()
    return b64encode(f.encrypt(value.encode())).decode()


def decrypt_value(encrypted_value):
    if not encrypted_value:
        return encrypted_value
    f = get_encryption_key()
    return f.decrypt(b64decode(encrypted_value)).decode()
