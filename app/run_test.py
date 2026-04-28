import os
from encryption import encrypt_file, decrypt_file
from aws_client import upload_file, download_file

# 1. Prepare a test file
TEST_DATA = b"This is a secret message for SCS project."
FILE_NAME = "test_secret.txt"
ENC_FILE = "test_secret.enc"
DECODER_FILE = "restored_secret.txt"

def run_full_test():
    # --- STEP A: LOCAL ENCRYPTION (Hexie/Client-side) ---
    print("🔒 Encrypting file locally...")
    ciphertext = encrypt_file(TEST_DATA) 
    with open(ENC_FILE, "wb") as f:
        f.write(ciphertext)

    # --- STEP B: UPLOAD TO AWS ---
    # Only the encrypted .enc file goes to the cloud 
    upload_file(ENC_FILE, ENC_FILE)

    # --- STEP C: DOWNLOAD FROM AWS ---
    print("\ncloud ☁️ -> local 🏠")
    download_file(ENC_FILE, "downloaded_temp.enc")

    # --- STEP D: DECRYPTION ---
    print("🔓 Decrypting file locally...")
    with open("downloaded_temp.enc", "rb") as f:
        downloaded_data = f.read()
    
    decrypted_plain = decrypt_file(downloaded_data)

    # --- VERIFICATION ---
    if decrypted_plain == TEST_DATA:
        print("\n🔥 SUCCESS: The retrieved file matches the original!")
        print(f"Original Content: {decrypted_plain.decode()}")
    else:
        print("\n❌ FAILURE: Data mismatch.")

if __name__ == "__main__":
    run_full_test()