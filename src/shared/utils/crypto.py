import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class LynkCrypto:
    """
    Lynk Payload Encryption using AES-GCM (256-bit).
    Provides both confidentiality and data integrity.
    """
    
    NONCE_SIZE = 12
    TAG_SIZE = 16

    def __init__(self, key_hex):
        try:
            # Explicitly cast to string in case YAML parser loads all-numeric keys as ints
            key_str = str(key_hex)
            # Key must be 32 bytes (256 bits)
            self.key = bytes.fromhex(key_str)
            if len(self.key) != 32:
                raise ValueError("Encryption key must be 32 bytes (64 hex characters)")
            self.aes_gcm = AESGCM(self.key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, data: bytes, associated_data: bytes = None) -> bytes:
        """
        Encrypts data and appends nonce + tag.
        Result: [Nonce (12)] + [Encrypted Data] + [Tag (16)]
        """
        nonce = os.urandom(self.NONCE_SIZE)
        # AESGCM.encrypt returns [encrypted_data + tag]
        ciphertext_with_tag = self.aes_gcm.encrypt(nonce, data, associated_data)
        return nonce + ciphertext_with_tag

    def decrypt(self, encrypted_data: bytes, associated_data: bytes = None) -> bytes:
        """
        Decrypts data using the prepended nonce.
        Input: [Nonce (12)] + [Encrypted Data] + [Tag (16)]
        """
        if len(encrypted_data) < self.NONCE_SIZE + self.TAG_SIZE:
            raise ValueError("Encrypted data too short")
        
        nonce = encrypted_data[:self.NONCE_SIZE]
        ciphertext = encrypted_data[self.NONCE_SIZE:]
        
        return self.aes_gcm.decrypt(nonce, ciphertext, associated_data)
