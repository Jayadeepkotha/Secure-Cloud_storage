import os
import sys
import json
from encryption import decrypt_file
from aws_client import download_file

DI_MAP = "local_di.json"

def perform_search(keyword):
    """Core logic: Finds matches in the local Inverted Index."""
    if not os.path.exists(DI_MAP):
        return []
    with open(DI_MAP, "r") as f:
        di = json.load(f)
    search_term = keyword.lower().strip()
    return di.get(search_term, [])

def decrypt_and_save(selected_item, keyword_context):
    """Core logic: Downloads, decrypts, and saves the file."""
    os.makedirs("downloads", exist_ok=True)
    local_enc_path = os.path.join("downloads", selected_item['s3_key'])
    
    if download_file(selected_item['s3_key'], local_enc_path):
        with open(local_enc_path, "rb") as f:
            enc_data = f.read()
        
        # Uses the filename/keyword context to derive the key
        plain_data = decrypt_file(enc_data, selected_item['original'])
        output_path = os.path.join("downloads", f"RESTORED_{selected_item['original']}")
        
        with open(output_path, "wb") as f:
            f.write(plain_data)
        return output_path
    return None

def run_search_interface(keyword):
    """The Terminal Interface (keeping your original workflow)."""
    matches = perform_search(keyword)
    if not matches:
        print(f"❌ No files found for: '{keyword}'")
        return

    print(f"\n--- Results for '{keyword}' ---")
    for i, item in enumerate(matches):
        print(f"[{i}] {item['original']} (S3 ID: {item['s3_key'][:12]}...)")

    try:
        choice = int(input("\nEnter the file number to download and decrypt: "))
        selected = matches[choice]
        result_path = decrypt_and_save(selected, keyword)
        if result_path:
            print(f"✅ Success! File restored to: {result_path}")
    except (ValueError, IndexError):
        print("❌ Invalid selection.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scs_search.py <keyword>")
    else:
        run_search_interface(sys.argv[1])