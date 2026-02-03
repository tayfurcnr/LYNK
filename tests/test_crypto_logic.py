from src.shared.utils.crypto import LynkCrypto
import binascii

def test_encryption_decryption():
    key_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    crypto = LynkCrypto(key_hex)
    
    payload = b"Hello LYNK Mesh!"
    ad = b"AD_TEST"
    
    print(f"Original Payload: {payload}")
    
    # Encrypt
    encrypted = crypto.encrypt(payload, ad)
    print(f"Encrypted (hex): {binascii.hexlify(encrypted).decode()}")
    print(f"Encrypted Length: {len(encrypted)} (Original={len(payload)}, Overhead={len(encrypted)-len(payload)})")
    
    # Decrypt
    decrypted = crypto.decrypt(encrypted, ad)
    print(f"Decrypted: {decrypted}")
    
    assert payload == decrypted, "Decryption failed!"
    print("\nSUCCESS: Encryption/Decryption verified.")

    # Test Corrupted Data
    corrupted = bytearray(encrypted)
    corrupted[-1] = (corrupted[-1] + 1) % 256
    try:
        crypto.decrypt(bytes(corrupted), ad)
        print("FAIL: Tamper detection failed!")
    except Exception as e:
        print(f"SUCCESS: Tamper detected correctly ({e})")

if __name__ == "__main__":
    test_encryption_decryption()
