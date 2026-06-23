import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class Vault:
    def __init__(self, master_key: str = None):
        # In a real app, use a proper KMS. Here we use a derived key from env.
        self.master_key = master_key or os.getenv("ENCRYPTION_KEY", "gateway-default-secret-key-12345")
        self.key = self._derive_key(self.master_key)
        self.aesgcm = AESGCM(self.key)

    def _derive_key(self, master_key: str) -> bytes:
        salt = b'gateway-salt-99' # In production, store salt with encrypted data
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(master_key.encode())

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt(self, encrypted_data: str) -> str:
        data = base64.b64decode(encrypted_data)
        nonce = data[:12]
        ciphertext = data[12:]
        decrypted = self.aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')

# Singleton instance
vault = Vault()
