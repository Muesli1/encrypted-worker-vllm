import base64
import hashlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class EncryptionHandler:
    def __init__(self, key: str, string_encoding: str = "utf-8"):
        self.string_encoding = string_encoding

        key_hash = hashlib.sha256(key.encode(self.string_encoding)).digest()
        encryption_key = key_hash[:16]
        iv_key = key_hash[16:]
        self.cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv_key), backend=default_backend())
        self.padding = padding.PKCS7(128)

    def encrypt(self, data: str) -> str:
        encryptor = self.cipher.encryptor()
        padder = self.padding.padder()
        padded = padder.update(data.encode(self.string_encoding)) + padder.finalize()
        ct = encryptor.update(padded) + encryptor.finalize()
        return base64.b64encode(ct).decode(self.string_encoding)

    def decrypt(self, data: str) -> str:
        data = base64.b64decode(data.encode(self.string_encoding))
        unpadder = self.padding.unpadder()
        decryptor = self.cipher.decryptor()
        try:
            padded = decryptor.update(data) + decryptor.finalize()
            return (unpadder.update(padded) + unpadder.finalize()).decode(self.string_encoding)
        except UnicodeDecodeError as e:
            raise ValueError("Invalid data, could not decrypt") from e