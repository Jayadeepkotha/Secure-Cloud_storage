import os
import sys
import json
import requests
from encryption import decrypt_file, derive_keys
from aws_client import download_file
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
STATE_FILE = "local_hexie_state.json"
EC2_HOSTNAME = os.getenv("EC2_HOSTNAME", "127.0.0.1")
EC2_URL = f"http://{EC2_HOSTNAME}:5000"

def load_json_state(filepath):
    """Loads the latest secret shares (pi) for keywords."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def perform_search(keyword):
    """Generates Trapdoor and queries the EC2 Cloud Index."""
    keyword = keyword.lower().strip()
    print(f"🔎 Searching for keyword: '{keyword}'")
    
    # 1. Derive search key (kt1) and get current local state (pi)
    kt1, _ = derive_keys(keyword)
    state = load_json_state(STATE_FILE)
    pi = state.get(keyword)

    if not pi:
        print(f"ℹ️ No local state found for '{keyword}'. Ensure the file was uploaded.")
        return []

    # 2. Send Trapdoor (kt1, pi) to EC2[cite: 1]
    print(f"📡 Sending Trapdoor to EC2...")
    try:
        response = requests.post(f"{EC2_URL}/search", json={
            "kt1": kt1.hex(),
            "pi": pi
        }, timeout=10)
        
        if response.status_code == 200:
            # Server returns a list of DICTS: [{'s3_key': '...', 'original': '...'}, ...][cite: 1]
            return response.json().get('results', [])
        else:
            print(f"❌ EC2 Error: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Connection to EC2 failed: {e}")
        return []

def decrypt_and_save(selected_item):
    """Downloads from S3 and decrypts using the original filename context[cite: 1]."""
    # Fix: Extract from dictionary returned by EC2[cite: 1]
    s3_key = selected_item['s3_key']
    original_name = selected_item['original']
    
    os.makedirs("downloads", exist_ok=True)
    local_enc_path = os.path.join("downloads", s3_key)
    
    print(f"☁️ Downloading from S3...")
    if download_file(s3_key, local_enc_path):
        with open(local_enc_path, "rb") as f:
            enc_data = f.read()
        
        print(f"🔓 Decrypting '{original_name}' locally...")
        try:
            # Algorithm 6: Decrypt locally using the derived session key[cite: 1]
            plain_data = decrypt_file(enc_data, original_name) 
            output_path = os.path.join("downloads", f"RESTORED_{original_name}")
            
            with open(output_path, "wb") as f:
                f.write(plain_data)
            
            os.remove(local_enc_path) # Cleanup encrypted temp file
            return output_path
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return None
    return None

def run_search_interface(keyword):
    """Terminal UI for the Hexie search process[cite: 1]."""
    matches = perform_search(keyword) 
    if not matches:
        print(f"❌ No matching records found for: '{keyword}'")
        return

    print(f"\n✅ Found {len(matches)} matching file(s) on EC2:")
    for i, item in enumerate(matches):
        # Fix: Access 'original' filename from the EC2 result dictionary[cite: 1]
        print(f"[{i}] {item['original']} (S3 ID: {item['s3_key'][:12]}...)")

    try:
        choice = int(input("\nEnter the file number to download: "))
        selected_item = matches[choice]
        result_path = decrypt_and_save(selected_item)
        if result_path:
            print(f"✨ Success! File restored to: {os.path.abspath(result_path)}")
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scs_search.py <keyword>")
    else:
        run_search_interface(sys.argv[1])