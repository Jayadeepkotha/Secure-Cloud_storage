from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, hmac
import os

# This is 'k' from the paper. Keep this secret locally.
MASTER_KEY = b'fixed_32_byte_key_for_testing_123' 

def derive_keys(keyword):
    """Function F: Derives session keys k1 (index) and k2 (data). """
    h = hmac.HMAC(MASTER_KEY, hashes.SHA256())
    h.update(keyword.encode())
    res = h.finalize()
    # k1 and k2 used for different parts of the encryption process
    return res[:16], res[16:]

def encrypt_file(data, keyword):
    """Algorithm 2: Encrypts data using k2 derived from the keyword. [cite: 306]"""
    _, k2 = derive_keys(keyword)
    aesgcm = AESGCM(k2)
    nonce = os.urandom(12)
    # Prefix with op=0 (insert) [cite: 290, 306]
    ciphertext = aesgcm.encrypt(nonce, b'\x00' + data, None)
    return nonce + ciphertext

def decrypt_file(encrypted_data, keyword):
    """Algorithm 6: Decrypts data locally on the client side. [cite: 405]"""
    _, k2 = derive_keys(keyword)
    aesgcm = AESGCM(k2)
    nonce = encrypted_data[:12]
    tag_ciphertext = encrypted_data[12:]
    # Removes the 'op' byte after decryption [cite: 405]
    return aesgcm.decrypt(nonce, tag_ciphertext, None)[1:]