import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib


class AESUtils:
    def __init__(self):
        # Default key and IV for AES encryption/decryption
        # These should match the ones used by the target application
        self.key = b"your_secret_key_here_32_bytes_!!"  # 32 bytes for AES-256
        self.iv = b"your_iv_here_16b"  # 16 bytes for AES IV
    
    def set_key(self, key: str):
        """Set custom encryption key"""
        if isinstance(key, str):
            key = key.encode('utf-8')
        # Ensure key is 32 bytes for AES-256
        if len(key) < 32:
            key = key.ljust(32, b'\x00')
        elif len(key) > 32:
            key = key[:32]
        self.key = key
    
    def set_iv(self, iv: str):
        """Set custom initialization vector"""
        if isinstance(iv, str):
            iv = iv.encode('utf-8')
        # Ensure IV is 16 bytes
        if len(iv) < 16:
            iv = iv.ljust(16, b'\x00')
        elif len(iv) > 16:
            iv = iv[:16]
        self.iv = iv
    
    def encrypt_aes_cbc(self, data: bytes) -> bytes:
        """Encrypt data using AES-256-CBC"""
        try:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            
            # Pad the data to be multiple of 16 bytes
            padded_data = pad(data, AES.block_size)
            
            # Encrypt the data
            encrypted_data = cipher.encrypt(padded_data)
            
            return encrypted_data
        except Exception as e:
            print(f"Encryption error: {e}")
            return data
    
    def decrypt_aes_cbc(self, encrypted_hex: str) -> bytes:
        """Decrypt hex-encoded encrypted data using AES-256-CBC"""
        try:
            # Convert hex string to bytes
            encrypted_data = bytes.fromhex(encrypted_hex)
            
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            
            # Decrypt the data
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Remove padding
            unpadded_data = unpad(decrypted_data, AES.block_size)
            
            return unpadded_data
        except Exception as e:
            print(f"Decryption error: {e}")
            # Return original data if decryption fails
            return bytes.fromhex(encrypted_hex)
    
    def generate_key_from_string(self, string_key: str) -> bytes:
        """Generate a 32-byte key from a string using SHA-256"""
        return hashlib.sha256(string_key.encode('utf-8')).digest()
    
    def generate_iv_from_string(self, string_iv: str) -> bytes:
        """Generate a 16-byte IV from a string using MD5"""
        return hashlib.md5(string_iv.encode('utf-8')).digest()